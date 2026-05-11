"""Core report generation pipeline — called by both the CLI and the Celery task.

Reads file paths from an Upload row, runs parsers → metrics → narrative → PDF,
then saves results back to the Report row.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.metrics.engine import MetricsEngine, MetricsInput
from app.models.report import Report
from app.models.upload import Upload
from app.narrative.generator import NarrativeGenerator
from app.parsers import (
    BalanceSheetParser,
    DebtorAgeParser,
    EmployeeCostParser,
    IncomeStatementParser,
    LeaveLiabilityParser,
    PayrollSummaryParser,
)
from app.reports.pdf_generator import generate_pdf

log = get_logger(__name__)


def _parse_file(parser_cls, path: str | None):
    """Parse a single export file. Returns None if path is absent or missing on disk."""
    if not path or not Path(path).exists():
        return None
    return parser_cls().parse(path)


def run_for_upload(upload_id: uuid.UUID, db: Session) -> Report:
    """Full pipeline for one Upload row. Returns the persisted Report."""
    upload = db.get(Upload, upload_id)
    if not upload:
        raise ValueError(f"Upload {upload_id} not found")

    _set_status(upload, "processing", db)

    try:
        report = _execute(upload, db)
        _set_status(upload, "complete", db)
        return report
    except Exception as exc:
        log.error("pipeline.failed", upload_id=str(upload_id), error=str(exc))
        _set_status(upload, "failed", db, error=str(exc))
        raise


def _execute(upload: Upload, db: Session) -> Report:
    warnings: list[str] = []

    def _parse(parser_cls, path_attr: str, label: str):
        path = getattr(upload, path_attr)
        if not path or not Path(path).exists():
            return None
        log.info("pipeline.parse", file=label, upload_id=str(upload.id))
        result = parser_cls().parse(path)
        warnings.extend(result.warnings)
        return result

    income  = _parse(IncomeStatementParser, "income_statement_path", "income_statement")
    balance = _parse(BalanceSheetParser, "balance_sheet_path", "balance_sheet")
    debtors = _parse(DebtorAgeParser, "debtors_age_path", "debtors_age")

    if not income or not balance or not debtors:
        raise ValueError(
            "Income statement, balance sheet, and debtor age analysis are required."
        )

    company = upload.company
    plan = (company.plan or "starter").lower()

    # Payroll data is Professional+ only
    payroll = None
    emp_cost = None
    leave = None
    if plan in ("professional", "premium"):
        payroll  = _parse(PayrollSummaryParser, "payroll_summary_path", "payroll_summary")
        emp_cost = _parse(EmployeeCostParser, "payroll_employee_cost_path", "employee_cost")
        leave    = _parse(LeaveLiabilityParser, "payroll_leave_path", "leave_liability")

    # Afrikaans language is Professional+ only
    language = getattr(company, "language", "en") or "en"
    if plan == "starter":
        language = "en"

    data = MetricsInput(
        period_month=upload.period_month,
        period_year=upload.period_year,
        company_name=company.trading_name or company.name,
        income_totals=income.totals,
        balance_totals=balance.totals,
        debtors_totals=debtors.totals,
        payroll_summary_totals=payroll.totals if payroll else None,
        payroll_employee_cost_totals=emp_cost.totals if emp_cost else None,
        payroll_leave_totals=leave.totals if leave else None,
        payroll_journal_integrated=upload.payroll_journal_integrated,
        warnings=warnings,
    )

    log.info("pipeline.metrics", upload_id=str(upload.id))
    metrics = MetricsEngine().run(data)

    # Premium: enrich metrics with YoY comparison and anomaly flags
    if plan == "premium":
        _enrich_premium(metrics, upload.company_id, upload.period_month, upload.period_year, db)

    log.info("pipeline.narrative", upload_id=str(upload.id))
    narrative = NarrativeGenerator().generate(metrics, language=language, plan=plan)

    log.info("pipeline.pdf", upload_id=str(upload.id))
    from app.core.config import settings
    pdf_path = generate_pdf(metrics, narrative, output_dir=settings.reports_dir)

    # Upsert Report row (one per company per period)
    from sqlalchemy import select
    existing = db.execute(
        select(Report).where(
            Report.company_id == upload.company_id,
            Report.period_month == upload.period_month,
            Report.period_year == upload.period_year,
        )
    ).scalar_one_or_none()

    if existing:
        report = existing
    else:
        report = Report(
            company_id=upload.company_id,
            upload_id=upload.id,
            period_month=upload.period_month,
            period_year=upload.period_year,
        )
        db.add(report)

    report.metrics = metrics
    report.narrative_summary = narrative.summary
    report.narrative_revenue = narrative.revenue
    report.narrative_costs = narrative.costs
    report.narrative_debtors = narrative.debtors
    report.narrative_payroll = narrative.payroll
    report.narrative_cash = narrative.cash
    report.narrative_actions = narrative.actions
    report.narrative_trend = narrative.trend
    report.pdf_path = str(pdf_path)
    report.payroll_pending = False  # Partner upload always includes everything at once
    report.generated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(report)
    log.info(
        "pipeline.done",
        report_id=str(report.id),
        health_score=metrics.get("health_score"),
    )
    return report


def run_for_agent_data(
    company_id: uuid.UUID,
    metrics_data: dict,
    period_month: int,
    period_year: int,
    db: Session,
) -> Report:
    """Pipeline for Evolution agent snapshots — no Upload row, metrics pre-computed by agent."""
    from sqlalchemy import select
    from app.core.config import settings
    from app.models.company import Company

    company = db.get(Company, company_id)
    if not company:
        raise ValueError(f"Company {company_id} not found")

    log.info(
        "pipeline.agent", company=company.name,
        period=f"{period_month}/{period_year}",
    )

    # Agent sends raw totals — run them through the metrics engine for health scoring
    from app.metrics.engine import MetricsEngine, MetricsInput

    data = MetricsInput(
        period_month=period_month,
        period_year=period_year,
        company_name=company.trading_name or company.name,
        income_totals=metrics_data.get("income_totals", {}),
        balance_totals=metrics_data.get("balance_totals", {}),
        debtors_totals=metrics_data.get("debtors_totals", {}),
        payroll_summary_totals=metrics_data.get("payroll_summary_totals"),
        payroll_employee_cost_totals=metrics_data.get("payroll_employee_cost_totals"),
        payroll_leave_totals=metrics_data.get("payroll_leave_totals"),
        payroll_journal_integrated=metrics_data.get("payroll_journal_integrated", False),
        warnings=[],
    )

    plan = (company.plan or "starter").lower()
    language = getattr(company, "language", "en") or "en"
    if plan == "starter":
        language = "en"
        data.payroll_summary_totals = None
        data.payroll_employee_cost_totals = None
        data.payroll_leave_totals = None

    # For Pro/Premium: check if bookkeeper has already uploaded payroll for this period
    payroll_pending = False
    if plan in ("professional", "premium"):
        from app.models.upload import Upload
        payroll_upload = db.execute(
            select(Upload).where(
                Upload.company_id == company_id,
                Upload.period_month == period_month,
                Upload.period_year == period_year,
                Upload.payroll_summary_path.is_not(None),
            )
        ).scalar_one_or_none()

        if payroll_upload:
            log.info("pipeline.agent.payroll_found", upload_id=str(payroll_upload.id))
            pr = _parse_file(PayrollSummaryParser, payroll_upload.payroll_summary_path)
            ec = _parse_file(EmployeeCostParser, payroll_upload.payroll_employee_cost_path)
            lv = _parse_file(LeaveLiabilityParser, payroll_upload.payroll_leave_path)
            data.payroll_summary_totals = pr.totals if pr else None
            data.payroll_employee_cost_totals = ec.totals if ec else None
            data.payroll_leave_totals = lv.totals if lv else None
        else:
            payroll_pending = True
            log.info("pipeline.agent.payroll_pending", company_id=str(company_id))

    metrics = MetricsEngine().run(data)

    if plan == "premium":
        _enrich_premium(metrics, company_id, period_month, period_year, db)

    narrative = NarrativeGenerator().generate(metrics, language=language, plan=plan)
    pdf_path = generate_pdf(metrics, narrative, output_dir=settings.reports_dir)

    # Upsert Report row
    existing = db.execute(
        select(Report).where(
            Report.company_id == company_id,
            Report.period_month == period_month,
            Report.period_year == period_year,
        )
    ).scalar_one_or_none()

    report = existing or Report(
        company_id=company_id,
        period_month=period_month,
        period_year=period_year,
    )
    if not existing:
        db.add(report)

    report.metrics = metrics
    report.narrative_summary = narrative.summary
    report.narrative_revenue = narrative.revenue
    report.narrative_costs = narrative.costs
    report.narrative_debtors = narrative.debtors
    report.narrative_payroll = narrative.payroll
    report.narrative_cash = narrative.cash
    report.narrative_actions = narrative.actions
    report.narrative_trend = narrative.trend
    report.pdf_path = str(pdf_path)
    report.payroll_pending = payroll_pending
    report.generated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(report)
    log.info(
        "pipeline.agent.done",
        report_id=str(report.id),
        health_score=metrics.get("health_score"),
    )
    return report


def apply_payroll_update(upload_id: uuid.UUID, db: Session) -> Report:
    """Merge payroll files from an Evolution payroll upload into an existing report.

    Called when the bookkeeper uploads payroll after the agent has already pushed
    accounting data and created a partial report with payroll_pending=True.
    """
    from sqlalchemy import select
    from app.core.config import settings
    from app.metrics import payroll as payroll_mod

    upload = db.get(Upload, upload_id)
    if not upload:
        raise ValueError(f"Upload {upload_id} not found")

    report = db.execute(
        select(Report).where(
            Report.company_id == upload.company_id,
            Report.period_month == upload.period_month,
            Report.period_year == upload.period_year,
        )
    ).scalar_one_or_none()
    if not report:
        raise ValueError(
            f"No report found for period {upload.period_month}/{upload.period_year}. "
            "The Evolution agent must push data before payroll can be applied."
        )

    company = upload.company
    plan = (company.plan or "starter").lower()
    language = getattr(company, "language", "en") or "en"
    if plan == "starter":
        language = "en"

    warnings: list[str] = []
    payroll = _parse_file(PayrollSummaryParser, upload.payroll_summary_path)
    emp_cost = _parse_file(EmployeeCostParser, upload.payroll_employee_cost_path)
    leave = _parse_file(LeaveLiabilityParser, upload.payroll_leave_path)
    for result in (payroll, emp_cost, leave):
        if result:
            warnings.extend(result.warnings)

    existing = dict(report.metrics or {})

    pay = payroll_mod.compute(
        payroll.totals if payroll else None,
        emp_cost.totals if emp_cost else None,
        leave.totals if leave else None,
        revenue_current=existing.get("revenue_current_month", 0),
        revenue_previous=existing.get("revenue_previous_month", 0),
        cash_balance=existing.get("cash_balance", 0),
        period_month=upload.period_month,
        period_year=upload.period_year,
        previous_payroll_gross=None,
        journal_integrated=upload.payroll_journal_integrated,
    )
    existing.update(pay)
    existing.update(MetricsEngine.score(existing))
    if warnings:
        existing["warnings"] = (existing.get("warnings") or []) + warnings

    narrative = NarrativeGenerator().generate(existing, language=language, plan=plan)
    pdf_path = generate_pdf(existing, narrative, output_dir=settings.reports_dir)

    report.metrics = existing
    report.narrative_summary = narrative.summary
    report.narrative_revenue = narrative.revenue
    report.narrative_costs = narrative.costs
    report.narrative_debtors = narrative.debtors
    report.narrative_payroll = narrative.payroll
    report.narrative_cash = narrative.cash
    report.narrative_actions = narrative.actions
    report.narrative_trend = narrative.trend
    report.pdf_path = str(pdf_path)
    report.payroll_pending = False

    db.commit()
    db.refresh(report)
    log.info("pipeline.payroll_applied", report_id=str(report.id))
    return report


def _enrich_premium(
    metrics: dict,
    company_id: uuid.UUID,
    period_month: int,
    period_year: int,
    db: Session,
) -> None:
    """Mutate metrics in-place with Premium-only data: YoY comparison and anomaly flags."""
    from sqlalchemy import select

    # Year-on-year comparison: fetch same month from prior year
    prior_year = db.execute(
        select(Report).where(
            Report.company_id == company_id,
            Report.period_month == period_month,
            Report.period_year == period_year - 1,
        )
    ).scalar_one_or_none()

    if prior_year and prior_year.metrics:
        pm = prior_year.metrics
        rev_now = metrics.get("revenue_current_month", 0)
        rev_then = pm.get("revenue_current_month", 0)
        gp_now = metrics.get("gross_profit_current", 0)
        gp_then = pm.get("gross_profit_current", 0)
        cost_now = metrics.get("total_costs_current", 0)
        cost_then = pm.get("total_costs_current", 0)

        def _pct(now: float, then: float) -> float | None:
            if then == 0:
                return None
            return round((now - then) / abs(then) * 100, 1)

        metrics["yoy_revenue_change_pct"] = _pct(rev_now, rev_then)
        metrics["yoy_gross_profit_change_pct"] = _pct(gp_now, gp_then)
        metrics["yoy_cost_change_pct"] = _pct(cost_now, cost_then)
        metrics["yoy_prior_year_revenue"] = rev_then
        metrics["yoy_prior_year_gross_profit"] = gp_then
        metrics["yoy_available"] = True
    else:
        metrics["yoy_available"] = False

    # Quarterly trend: only on quarter-end months (March, June, September, December)
    if period_month in (3, 6, 9, 12):
        q_start = period_month - 2
        q_reports = db.execute(
            select(Report).where(
                Report.company_id == company_id,
                Report.period_year == period_year,
                Report.period_month.in_([q_start, q_start + 1, period_month]),
            )
        ).scalars().all()
        q_revenue = sum(
            (r.metrics or {}).get("revenue_current_month", 0) for r in q_reports
        )
        metrics["quarterly_revenue"] = q_revenue
        metrics["quarterly_period"] = f"Q{period_month // 3} {period_year}"

    # Anomaly detection
    anomalies: list[str] = []
    if metrics.get("revenue_change_pct", 0) < -20:
        anomalies.append(
            f"Revenue fell {abs(metrics['revenue_change_pct']):.1f}% versus last month — unusual drop"
        )
    top_mover_pct = metrics.get("top_cost_mover_change_pct", 0)
    if top_mover_pct > 30:
        anomalies.append(
            f"{metrics.get('top_cost_mover', 'A cost category')} spiked {top_mover_pct:.0f}% — review urgently"
        )
    if metrics.get("cash_runway_weeks", 999) < 6:
        anomalies.append(
            f"Cash runway is critically low at {metrics.get('cash_runway_weeks', 0):.1f} weeks"
        )
    if metrics.get("payroll_change_pct", 0) > 15:
        anomalies.append(
            f"Payroll jumped {metrics['payroll_change_pct']:.1f}% this month — investigate cause"
        )
    metrics["anomalies"] = anomalies


def _set_status(upload: Upload, status: str, db: Session, error: str | None = None) -> None:
    upload.status = status
    if error:
        upload.error_message = error[:2000]
    db.commit()
