"""Metrics engine — combines parsed data into the full report metrics JSON.

Every metric the report needs (per CLAUDE.md spec) is produced here. The
output dict is what gets stored in `reports.metrics` JSONB and what the LLM
narrative + PDF templates render against.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import cash, costs, creditors, debtors, payroll, ratios, revenue


@dataclass
class MetricsInput:
    """Bundle of parsed totals for one reporting period."""

    period_month: int
    period_year: int
    company_name: str

    income_totals: dict[str, Any]
    balance_totals: dict[str, Any]
    debtors_totals: dict[str, Any]
    creditors_totals: dict[str, Any] = field(default_factory=dict)

    payroll_summary_totals: dict[str, Any] | None = None
    payroll_employee_cost_totals: dict[str, Any] | None = None
    payroll_leave_totals: dict[str, Any] | None = None
    payroll_journal_integrated: bool = False
    previous_payroll_gross: float | None = None

    warnings: list[str] = field(default_factory=list)


class MetricsEngine:
    """Stateless orchestrator. Call :meth:`run` with a MetricsInput."""

    def run(self, data: MetricsInput) -> dict[str, Any]:
        rev = revenue.compute(data.income_totals)
        cst = costs.compute(data.income_totals)
        rat = ratios.compute(data.income_totals)
        cred = creditors.compute(data.creditors_totals, cst["total_costs_current"])
        deb = debtors.compute(data.debtors_totals, rev["revenue_current_month"])
        cash_metrics = cash.compute(
            data.balance_totals, monthly_costs=cst["total_costs_current"]
        )
        pay = payroll.compute(
            data.payroll_summary_totals,
            data.payroll_employee_cost_totals,
            data.payroll_leave_totals,
            revenue_current=rev["revenue_current_month"],
            revenue_previous=rev["revenue_previous_month"],
            cash_balance=cash_metrics["cash_balance"],
            period_month=data.period_month,
            period_year=data.period_year,
            previous_payroll_gross=data.previous_payroll_gross,
            journal_integrated=data.payroll_journal_integrated,
        )

        out: dict[str, Any] = {}
        out.update(rev)
        out.update(rat)
        out.update(cst)
        out.update(deb)
        out.update(cash_metrics)
        out.update(pay)
        out.update(cred)

        out.update(_health_score(out))

        out["company_name"] = data.company_name
        out["period_month"] = data.period_month
        out["period_year"] = data.period_year
        out["warnings"] = data.warnings
        return out


# ---------------------------------------------------------------------------
# Health score
# ---------------------------------------------------------------------------


_RATING = [
    (85, "excellent"),
    (70, "good"),
    (55, "fair"),
    (35, "poor"),
    (0, "critical"),
]


def _health_score(m: dict[str, Any]) -> dict[str, Any]:
    """Composite 0–100 health score and human flags."""
    score = 100.0
    flags: list[str] = []

    # Revenue trend (-30 max)
    if m["revenue_trend"] == "declining":
        delta_pen = min(20, abs(m["revenue_change_pct"]) * 0.5)
        score -= 10 + delta_pen
        flags.append(
            f"Revenue declined {abs(m['revenue_change_pct']):.1f}% versus last month"
        )
    elif m["revenue_trend"] == "growing":
        score += 5

    # Margin (-15 max)
    if m["gross_margin_pct"] < 20:
        score -= 15
        flags.append(f"Gross margin is low at {m['gross_margin_pct']:.1f}%")
    elif m["gross_margin_pct"] < 35:
        score -= 5

    # Debtors (-20 max)
    if m["debtors_health"] == "critical":
        score -= 20
        flags.append(
            f"{m['overdue_invoices_count']} overdue invoice(s) worth "
            f"R{m['overdue_invoices_value']:,.0f}"
        )
    elif m["debtors_health"] == "warning":
        score -= 10
        flags.append(
            f"{m['overdue_invoices_count']} invoice(s) overdue 60+ days"
        )

    # Cash (-25 max)
    if m["cash_health"] == "critical":
        score -= 25
        flags.append(
            f"Cash runway only {m['cash_runway_weeks']:.1f} weeks at current burn"
        )
    elif m["cash_health"] == "warning":
        score -= 10
        flags.append(f"Cash runway below 12 weeks ({m['cash_runway_weeks']:.1f})")

    # Payroll (-25 max)
    if m["payroll_health"] == "critical":
        score -= 25
        flags.append("Cash on hand is less than 1.5x next payroll run")
    elif m["payroll_health"] == "warning":
        score -= 10
        if m["payroll_pct_of_revenue"] > 40:
            flags.append(
                f"Payroll is {m['payroll_pct_of_revenue']:.1f}% of revenue — high"
            )
        if m["payroll_change_pct"] > 10:
            flags.append(
                f"Payroll grew {m['payroll_change_pct']:.1f}% versus last month"
            )

    # Top cost mover signal
    if m.get("top_cost_mover") and m.get("top_cost_mover_change_pct", 0) > 25:
        flags.append(
            f"{m['top_cost_mover']} jumped {m['top_cost_mover_change_pct']:.0f}% "
            f"(R{m['top_cost_mover_change']:,.0f})"
        )

    score = max(0.0, min(100.0, score))
    rating = next(label for threshold, label in _RATING if score >= threshold)

    return {
        "health_score": round(score),
        "health_rating": rating,
        "health_flags": flags,
    }
