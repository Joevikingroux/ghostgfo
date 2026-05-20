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


def _redact_pii(metrics: dict) -> dict:
    """Remove personal names from stored metrics after the PDF has been generated.

    The PDF (delivered to the owner) retains all names. The database copy
    keeps only amounts so a breach doesn't expose client business relationships.
    """
    m = dict(metrics)
    if isinstance(m.get("worst_offenders"), list):
        m["worst_offenders"] = [
            {**e, "name": "[redacted]"} for e in m["worst_offenders"]
        ]
    if isinstance(m.get("top_creditors"), list):
        m["top_creditors"] = [
            {**e, "name": "[redacted]"} for e in m["top_creditors"]
        ]
    return m


def _parse_file(parser_cls, path: str | None):
    """Parse a single export file. Returns None if path is absent or missing on disk."""
    if not path or not Path(path).exists():
        return None
    return parser_cls().parse(path)


def _get_prior_metrics(
    company_id: uuid.UUID,
    period_month: int,
    period_year: int,
    db: Session,
) -> dict | None:
    """Return the metrics dict from the immediately preceding month's report, or None."""
    from sqlalchemy import select

    if period_month == 1:
        prior_month, prior_year = 12, period_year - 1
    else:
        prior_month, prior_year = period_month - 1, period_year

    prior = db.execute(
        select(Report).where(
            Report.company_id == company_id,
            Report.period_month == prior_month,
            Report.period_year == prior_year,
        )
    ).scalar_one_or_none()

    return dict(prior.metrics) if prior and prior.metrics else None


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

    income = _parse(IncomeStatementParser, "income_statement_path", "income_statement")
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
        payroll = _parse(
            PayrollSummaryParser, "payroll_summary_path", "payroll_summary"
        )
        emp_cost = _parse(
            EmployeeCostParser, "payroll_employee_cost_path", "employee_cost"
        )
        leave = _parse(LeaveLiabilityParser, "payroll_leave_path", "leave_liability")

    # Afrikaans language is Professional+ only
    language = getattr(company, "language", "en") or "en"
    if plan == "starter":
        language = "en"

    # Prior month data enables payroll change % and headcount delta
    prior = _get_prior_metrics(
        upload.company_id, upload.period_month, upload.period_year, db
    )
    prior_payroll_gross = prior.get("payroll_gross_total") if prior else None
    prior_headcount = (
        int(prior["payroll_headcount"])
        if prior and prior.get("payroll_headcount") is not None
        else None
    )

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
        previous_payroll_gross=prior_payroll_gross,
        previous_headcount=prior_headcount,
        warnings=warnings,
    )

    log.info("pipeline.metrics", upload_id=str(upload.id))
    metrics = MetricsEngine().run(data)

    # Premium: enrich metrics with YoY comparison and anomaly flags
    if plan == "premium":
        _enrich_premium(
            metrics, upload.company_id, upload.period_month, upload.period_year, db
        )

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

    report.metrics = _redact_pii(metrics)
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
    report.ai_generated = narrative.ai_generated
    report.ai_model = narrative.ai_model
    report.ai_tokens_used = narrative.ai_tokens_used
    report.generated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(report)
    log.info(
        "pipeline.done",
        report_id=str(report.id),
        health_score=metrics.get("health_score"),
        ai_generated=narrative.ai_generated,
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
        "pipeline.agent",
        company=company.name,
        period=f"{period_month}/{period_year}",
    )

    # Agent sends raw totals — run them through the metrics engine for health scoring
    from app.metrics.engine import MetricsEngine, MetricsInput

    # Prior month data enables payroll change % and headcount delta
    prior = _get_prior_metrics(company_id, period_month, period_year, db)
    prior_payroll_gross = prior.get("payroll_gross_total") if prior else None
    prior_headcount = (
        int(prior["payroll_headcount"])
        if prior and prior.get("payroll_headcount") is not None
        else None
    )

    data = MetricsInput(
        period_month=period_month,
        period_year=period_year,
        company_name=company.trading_name or company.name,
        income_totals=metrics_data.get("income_totals", {}),
        balance_totals=metrics_data.get("balance_totals", {}),
        debtors_totals=metrics_data.get("debtors_totals", {}),
        creditors_totals=metrics_data.get("creditors_totals", {}),
        payroll_summary_totals=metrics_data.get("payroll_summary_totals"),
        payroll_employee_cost_totals=metrics_data.get("payroll_employee_cost_totals"),
        payroll_leave_totals=metrics_data.get("payroll_leave_totals"),
        payroll_journal_integrated=metrics_data.get(
            "payroll_journal_integrated", False
        ),
        previous_payroll_gross=prior_payroll_gross,
        previous_headcount=prior_headcount,
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
            ec = _parse_file(
                EmployeeCostParser, payroll_upload.payroll_employee_cost_path
            )
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

    # Pass through Evolution-only extras (sales items) from the agent payload
    sales_items = metrics_data.get("sales_items")
    if sales_items:
        metrics["top_sales_by_value"] = sales_items.get("top_by_value", [])
        metrics["top_sales_by_qty"] = sales_items.get("top_by_qty", [])

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

    report.metrics = _redact_pii(metrics)
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
    report.ai_generated = narrative.ai_generated
    report.ai_model = narrative.ai_model
    report.ai_tokens_used = narrative.ai_tokens_used
    report.generated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(report)
    log.info(
        "pipeline.agent.done",
        report_id=str(report.id),
        health_score=metrics.get("health_score"),
        ai_generated=narrative.ai_generated,
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

    prior = _get_prior_metrics(
        upload.company_id, upload.period_month, upload.period_year, db
    )
    prior_payroll_gross = prior.get("payroll_gross_total") if prior else None
    prior_headcount = (
        int(prior["payroll_headcount"])
        if prior and prior.get("payroll_headcount") is not None
        else None
    )

    pay = payroll_mod.compute(
        payroll.totals if payroll else None,
        emp_cost.totals if emp_cost else None,
        leave.totals if leave else None,
        revenue_current=existing.get("revenue_current_month", 0),
        revenue_previous=existing.get("revenue_previous_month", 0),
        cash_balance=existing.get("cash_balance", 0),
        period_month=upload.period_month,
        period_year=upload.period_year,
        previous_payroll_gross=prior_payroll_gross,
        previous_headcount=prior_headcount,
        journal_integrated=upload.payroll_journal_integrated,
    )
    existing.update(pay)
    existing.update(MetricsEngine.score(existing))
    if warnings:
        existing["warnings"] = (existing.get("warnings") or []) + warnings

    narrative = NarrativeGenerator().generate(existing, language=language, plan=plan)
    pdf_path = generate_pdf(existing, narrative, output_dir=settings.reports_dir)

    report.metrics = _redact_pii(existing)
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
    report.ai_generated = narrative.ai_generated
    report.ai_model = narrative.ai_model
    report.ai_tokens_used = narrative.ai_tokens_used

    db.commit()
    db.refresh(report)
    log.info(
        "pipeline.payroll_applied",
        report_id=str(report.id),
        ai_generated=narrative.ai_generated,
    )
    return report


def _enrich_premium(
    metrics: dict,
    company_id: uuid.UUID,
    period_month: int,
    period_year: int,
    db: Session,
) -> None:
    """Mutate metrics in-place with Premium-only data: YoY comparison and anomaly flags."""
    from sqlalchemy import and_, or_, select

    def _pct(now: float, then: float) -> float | None:
        if then == 0:
            return None
        return round((now - then) / abs(then) * 100, 1)

    # Year-on-year comparison: fetch same month from prior two years
    prior_y1 = db.execute(
        select(Report).where(
            Report.company_id == company_id,
            Report.period_month == period_month,
            Report.period_year == period_year - 1,
        )
    ).scalar_one_or_none()

    prior_y2 = db.execute(
        select(Report).where(
            Report.company_id == company_id,
            Report.period_month == period_month,
            Report.period_year == period_year - 2,
        )
    ).scalar_one_or_none()

    if prior_y1 and prior_y1.metrics:
        pm = prior_y1.metrics
        rev_now = metrics.get("revenue_current_month", 0)
        rev_then = pm.get("revenue_current_month", 0)
        gp_now = metrics.get("gross_profit_current", 0)
        gp_then = pm.get("gross_profit_current", 0)
        cost_now = metrics.get("total_costs_current", 0)
        cost_then = pm.get("total_costs_current", 0)

        metrics["yoy_revenue_change_pct"] = _pct(rev_now, rev_then)
        metrics["yoy_gross_profit_change_pct"] = _pct(gp_now, gp_then)
        metrics["yoy_cost_change_pct"] = _pct(cost_now, cost_then)
        metrics["yoy_prior_year_revenue"] = rev_then
        metrics["yoy_prior_year_gross_profit"] = gp_then
        metrics["yoy_available"] = True

        # Two-year comparison for richer trend narrative
        if prior_y2 and prior_y2.metrics:
            pm2 = prior_y2.metrics
            metrics["yoy2_revenue_change_pct"] = _pct(
                rev_then, pm2.get("revenue_current_month", 0)
            )
            metrics["yoy2_prior_year_revenue"] = pm2.get("revenue_current_month", 0)
    else:
        metrics["yoy_available"] = False

    # Rolling 3-month quarterly: works for every month, handles year boundary
    q_filters = []
    m, y = period_month, period_year
    for _ in range(3):
        q_filters.append(and_(Report.period_month == m, Report.period_year == y))
        m -= 1
        if m == 0:
            m, y = 12, y - 1

    q_reports = (
        db.execute(
            select(Report).where(
                Report.company_id == company_id,
                or_(*q_filters),
            )
        )
        .scalars()
        .all()
    )

    q_revenue = sum(
        (r.metrics or {}).get("revenue_current_month", 0) for r in q_reports
    )
    q_gross_profit = sum(
        (r.metrics or {}).get("gross_profit_current", 0) for r in q_reports
    )
    q_costs = sum((r.metrics or {}).get("total_costs_current", 0) for r in q_reports)

    if period_month in (3, 6, 9, 12):
        q_label = f"Q{period_month // 3} {period_year}"
    else:
        q_label = f"Rolling 3M to {period_month:02d}/{period_year}"

    metrics["quarterly_revenue"] = q_revenue
    metrics["quarterly_gross_profit"] = q_gross_profit
    metrics["quarterly_costs"] = q_costs
    metrics["quarterly_period"] = q_label

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


def _set_status(
    upload: Upload, status: str, db: Session, error: str | None = None
) -> None:
    upload.status = status
    if error:
        upload.error_message = error[:2000]
    db.commit()
