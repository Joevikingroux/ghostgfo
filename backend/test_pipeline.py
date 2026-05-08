"""CLI end-to-end test: parse sample data → metrics → narrative → PDF.

Usage:
    python test_pipeline.py
    python test_pipeline.py --input ../sample_data --output ../sample_data/output
    python test_pipeline.py --input ../sample_data --output ../sample_data/output --lang af

No database or Celery required. Runs the full pipeline in-process.
Set OPENROUTER_API_KEY in .env (or environment) to get a real LLM narrative.
Without it the pipeline still completes using the built-in stub narrator.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow running from backend/ without installing as a package
sys.path.insert(0, str(Path(__file__).parent))

import click

from app.core.logging import configure_logging, get_logger

configure_logging()
log = get_logger("pipeline")


@click.command()
@click.option(
    "--input",
    "input_dir",
    default=str(Path(__file__).parent.parent / "sample_data"),
    show_default=True,
    help="Directory containing the sample CSV export files.",
)
@click.option(
    "--output",
    "output_dir",
    default=str(Path(__file__).parent.parent / "sample_data" / "output"),
    show_default=True,
    help="Directory where the PDF will be written.",
)
@click.option(
    "--company",
    default="ABC Hardware (Pty) Ltd",
    show_default=True,
    help="Company display name used in the report.",
)
@click.option(
    "--month",
    default=10,
    type=int,
    show_default=True,
    help="Reporting period month (1–12).",
)
@click.option(
    "--year",
    default=2025,
    type=int,
    show_default=True,
    help="Reporting period year.",
)
@click.option(
    "--lang",
    default="en",
    type=click.Choice(["en", "af"]),
    show_default=True,
    help="Narrative language.",
)
def run(
    input_dir: str,
    output_dir: str,
    company: str,
    month: int,
    year: int,
    lang: str,
) -> None:
    inp = Path(input_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    click.echo(f"\n Ghost CFO Pipeline — {company} {month:02d}/{year}\n")
    click.echo(f"  Input:  {inp}")
    click.echo(f"  Output: {out}\n")

    # -----------------------------------------------------------------------
    # 1. PARSE
    # -----------------------------------------------------------------------
    from app.parsers import (
        BalanceSheetParser,
        DebtorAgeParser,
        EmployeeCostParser,
        IncomeStatementParser,
        LeaveLiabilityParser,
        PayrollSummaryParser,
    )

    def _parse(parser_cls, pattern: str, label: str):
        matches = list(inp.glob(pattern))
        if not matches:
            click.echo(f"  [SKIP] {label} — no file matching '{pattern}'")
            return None
        path = matches[0]
        click.echo(f"  [PARSE] {label} — {path.name}")
        result = parser_cls().parse(path)
        for w in result.warnings:
            click.echo(f"    ⚠  {w}")
        return result

    income_result  = _parse(IncomeStatementParser, "income_statement_*.csv", "Income Statement")
    balance_result = _parse(BalanceSheetParser, "balance_sheet_*.csv", "Balance Sheet")
    debtors_result = _parse(DebtorAgeParser, "debtors_age_*.csv", "Debtor Age Analysis")
    payroll_result = _parse(PayrollSummaryParser, "payroll_summary_*.csv", "Payroll Summary")
    emp_cost_result = _parse(EmployeeCostParser, "payroll_employee_cost_*.csv", "Employee Cost")
    leave_result   = _parse(LeaveLiabilityParser, "payroll_leave_*.csv", "Leave Liability")

    if not income_result or not balance_result or not debtors_result:
        click.echo("\n  [ERROR] Missing required files. Aborting.", err=True)
        sys.exit(1)

    # -----------------------------------------------------------------------
    # 2. METRICS
    # -----------------------------------------------------------------------
    click.echo("\n  [METRICS] Computing financial metrics...")
    from app.metrics import MetricsEngine, MetricsInput

    data = MetricsInput(
        period_month=month,
        period_year=year,
        company_name=company,
        income_totals=income_result.totals,
        balance_totals=balance_result.totals,
        debtors_totals=debtors_result.totals,
        payroll_summary_totals=payroll_result.totals if payroll_result else None,
        payroll_employee_cost_totals=emp_cost_result.totals if emp_cost_result else None,
        payroll_leave_totals=leave_result.totals if leave_result else None,
        warnings=(
            income_result.warnings
            + balance_result.warnings
            + debtors_result.warnings
        ),
    )
    metrics = MetricsEngine().run(data)

    click.echo(f"    Revenue:       R{metrics['revenue_current_month']:>12,.0f}  "
               f"({metrics['revenue_change_pct']:+.1f}% vs prev)")
    click.echo(f"    Gross margin:  {metrics['gross_margin_pct']:.1f}%")
    click.echo(f"    Cash balance:  R{metrics['cash_balance']:>12,.0f}  "
               f"({metrics['cash_runway_weeks']:.1f} weeks runway)")
    if metrics.get("payroll_gross_total"):
        click.echo(f"    Payroll:       R{metrics['payroll_gross_total']:>12,.0f}  "
                   f"({metrics['payroll_pct_of_revenue']:.1f}% of revenue)")
        click.echo(f"    Leave liab:    R{metrics['leave_liability_rand']:>12,.0f}  "
                   f"({metrics['leave_liability_weeks_payroll']:.1f} weeks of payroll)")
    click.echo(f"    Health score:  {metrics['health_score']}/100 ({metrics['health_rating']})")
    for flag in metrics.get("health_flags", []):
        click.echo(f"      ⚑  {flag}")

    # -----------------------------------------------------------------------
    # 3. NARRATIVE
    # -----------------------------------------------------------------------
    click.echo(f"\n  [NARRATIVE] Generating narrative (lang={lang})...")
    from app.narrative.generator import NarrativeGenerator

    narrative = NarrativeGenerator().generate(metrics, language=lang)
    click.echo(f"    Summary: {narrative.summary[:120]}...")

    # -----------------------------------------------------------------------
    # 4. PDF
    # -----------------------------------------------------------------------
    click.echo("\n  [PDF] Rendering report...")
    from app.reports.pdf_generator import generate_pdf

    pdf_path = generate_pdf(metrics, narrative, output_dir=out)
    click.echo(f"\n  ✓ Done — {pdf_path}\n")


if __name__ == "__main__":
    run()
