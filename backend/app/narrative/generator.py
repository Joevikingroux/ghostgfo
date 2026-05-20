"""Narrative generator — calls the LLM for each report section.

Falls back to a deterministic stub when OPENROUTER_API_KEY is empty, so the
pipeline can be tested end-to-end without spending API credits.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger
from app.narrative import prompts
from app.narrative.tone import LANG_EN, currency

log = get_logger(__name__)

SECTIONS = [
    "summary",
    "revenue",
    "costs",
    "debtors",
    "payroll",
    "cash",
    "actions",
    "trend",
]


@dataclass
class Narrative:
    summary: str
    revenue: str
    costs: str
    debtors: str
    payroll: str
    cash: str
    actions: str
    trend: str = ""
    ai_generated: bool = False
    ai_model: str | None = None
    ai_tokens_used: int | None = None


class NarrativeGenerator:
    def generate(
        self,
        metrics: dict[str, Any],
        *,
        language: str = LANG_EN,
        plan: str = "starter",
    ) -> Narrative:
        plan = (plan or "starter").lower()

        if not settings.openrouter_api_key:
            log.warning("narrative.stub_mode", reason="OPENROUTER_API_KEY not set")
            return _stub_narrative(metrics, plan=plan)

        from app.narrative.openrouter import chat_completion

        parts: dict[str, str] = {}
        total_tokens = 0
        ai_success = False
        model_used = settings.openrouter_model

        for section in SECTIONS:
            # Gate payroll section to Professional+
            if section == "payroll" and plan == "starter":
                parts[section] = ""
                continue
            # Trend section only for Premium
            if section == "trend" and plan != "premium":
                parts[section] = ""
                continue
            if section == "summary":
                msgs = prompts.build_summary_prompt(metrics, lang=language)
            else:
                msgs = prompts.build_section_prompt(section, metrics, lang=language)
            try:
                content, tokens = chat_completion(msgs)
                parts[section] = content
                total_tokens += tokens
                ai_success = True
            except Exception as exc:
                log.error("narrative.llm_error", section=section, error=str(exc))
                parts[section] = _stub_section(section, metrics, plan=plan)

        if not ai_success:
            # Every LLM call failed — notify admin
            from app.core.admin_notify import notify_admin

            company = metrics.get("company_name", "unknown")
            notify_admin(
                "AI narrative generation failed",
                f"All LLM calls failed for company '{company}' "
                f"({metrics.get('period_month')}/{metrics.get('period_year')}). "
                f"Report was generated with stub narratives.",
            )

        return Narrative(
            **parts,
            ai_generated=ai_success,
            ai_model=model_used if ai_success else None,
            ai_tokens_used=total_tokens if ai_success else None,
        )


# ---------------------------------------------------------------------------
# Deterministic stub — used when no API key is present
# ---------------------------------------------------------------------------


def _stub_section(section: str, m: dict[str, Any], *, plan: str = "starter") -> str:
    name = m.get("company_name", "the business")
    month = m.get("period_month", "?")
    year = m.get("period_year", "?")

    if section == "summary":
        return (
            f"{name} — {month}/{year} Financial Report. "
            f"Revenue came in at {currency(m.get('revenue_current_month', 0))}, "
            f"a {abs(m.get('revenue_change_pct', 0)):.1f}% "
            f"{'decrease' if m.get('revenue_change_pct', 0) < 0 else 'increase'} "
            f"versus last month. "
            f"Overall health score: {m.get('health_score', 0)}/100 "
            f"({m.get('health_rating', 'unknown')})."
        )
    if section == "revenue":
        return (
            f"Revenue for {month}/{year} was "
            f"{currency(m.get('revenue_current_month', 0))}, "
            f"compared to {currency(m.get('revenue_previous_month', 0))} last month "
            f"({m.get('revenue_change_pct', 0):+.1f}%). "
            f"Year-to-date total: {currency(m.get('revenue_ytd', 0))}."
        )
    if section == "costs":
        return (
            f"Total costs this month: {currency(m.get('total_costs_current', 0))}. "
            f"Gross margin is {m.get('gross_margin_pct', 0):.1f}%. "
            + (
                f"The biggest cost mover was {m['top_cost_mover']} "
                f"({m.get('top_cost_mover_change_pct', 0):+.0f}%)."
                if m.get("top_cost_mover")
                else ""
            )
        )
    if section == "debtors":
        return (
            f"Customers owe {currency(m.get('debtors_total', 0))} in total. "
            f"{m.get('overdue_invoices_count', 0)} invoice(s) are overdue, "
            f"worth {currency(m.get('overdue_invoices_value', 0))}. "
            f"Debtor days: {m.get('debtor_days', 0):.0f}."
        )
    if section == "payroll":
        if plan == "starter":
            return ""
        if m.get("payroll_gross_total", 0) == 0:
            return "No payroll data was provided for this period."
        return (
            f"Gross payroll: {currency(m.get('payroll_gross_total', 0))} "
            f"covering {m.get('payroll_headcount', 0)} employees. "
            f"True employer cost (including UIF and SDL): "
            f"{currency(m.get('payroll_true_employer_cost', 0))} "
            f"({m.get('payroll_pct_of_revenue', 0):.1f}% of revenue). "
            f"Leave liability: {currency(m.get('leave_liability_rand', 0))}."
        )
    if section == "cash":
        return (
            f"Bank balance: {currency(m.get('cash_balance', 0))}. "
            f"At current spending the business has approximately "
            f"{m.get('cash_runway_weeks', 0):.1f} weeks of cash remaining. "
            f"Cash health: {m.get('cash_health', 'unknown')}."
        )
    if section == "actions":
        lines = ["Recommended actions this month:"]
        n = 1
        if not m.get("cash_covers_payroll"):
            lines.append(
                f"{n}. Collect outstanding debts urgently — next payroll is not "
                f"fully covered by cash on hand."
            )
            n += 1
        if m.get("overdue_invoices_count", 0) > 0:
            lines.append(
                f"{n}. Contact the {m['overdue_invoices_count']} overdue customer(s) "
                f"to collect {currency(m.get('overdue_invoices_value', 0))} this week."
            )
            n += 1
        if m.get("cash_health") in ("critical", "warning"):
            lines.append(
                f"{n}. Review discretionary spending to extend cash runway beyond "
                f"{m.get('cash_runway_weeks', 0):.1f} weeks."
            )
            n += 1
        if m.get("payroll_pct_of_revenue", 0) > 40:
            lines.append(
                f"{n}. Payroll is {m['payroll_pct_of_revenue']:.1f}% of revenue — "
                f"review staffing costs before next hire."
            )
            n += 1
        if n == 1:
            lines.append("1. Continue monitoring debtor days and cash runway weekly.")
        return "\n".join(lines)
    if section == "trend":
        if plan != "premium" or not m.get("yoy_available"):
            return ""
        yoy_rev = m.get("yoy_revenue_change_pct")
        prior_rev = m.get("yoy_prior_year_revenue", 0)
        year = m.get("period_year", "")
        prior_year = int(year) - 1 if year else ""
        q_rev = m.get("quarterly_revenue")
        q_period = m.get("quarterly_period", "")
        parts = [
            f"Year-on-year comparison ({prior_year} vs {year}): "
            f"revenue was {currency(prior_rev)} in the same month last year"
            + (f", a {yoy_rev:+.1f}% change." if yoy_rev is not None else "."),
        ]
        if q_rev:
            parts.append(f"{q_period} total revenue to date: {currency(q_rev)}.")
        anomalies = m.get("anomalies", [])
        if anomalies:
            parts.append("Anomalies detected: " + "; ".join(anomalies) + ".")
        return " ".join(parts)
    return f"[{section} section not yet generated]"


def _stub_narrative(m: dict[str, Any], *, plan: str = "starter") -> Narrative:
    return Narrative(
        **{section: _stub_section(section, m, plan=plan) for section in SECTIONS}
    )
