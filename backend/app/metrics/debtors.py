"""Debtor metrics: aging, collection days, health."""

from __future__ import annotations

from typing import Any

from app.metrics._helpers import round_money, round_pct, safe_div


def compute(
    debtors_totals: dict[str, Any],
    revenue_current: float,
) -> dict[str, Any]:
    total = float(debtors_totals.get("debtors_total", 0.0))
    over_90 = float(debtors_totals.get("debtors_over_90", 0.0))
    days_60 = float(debtors_totals.get("debtors_61_90", 0.0))
    overdue_value = float(debtors_totals.get("overdue_invoices_value", 0.0))
    overdue_count = int(debtors_totals.get("overdue_invoices_count", 0))

    # Approximate debtor days: outstanding / monthly revenue * 30
    debtor_days = safe_div(total, revenue_current) * 30 if revenue_current else 0.0

    overdue_share = safe_div(over_90 + days_60, total) if total else 0.0
    if overdue_share > 0.30 or over_90 > revenue_current * 0.10:
        health = "critical"
    elif overdue_share > 0.15 or overdue_count >= 3:
        health = "warning"
    else:
        health = "good"

    return {
        "debtors_total": round_money(total),
        "debtors_current": round_money(
            float(debtors_totals.get("debtors_current", 0.0))
        ),
        "debtors_30_60_days": round_money(
            float(debtors_totals.get("debtors_30_60", 0.0))
        ),
        "debtors_61_90_days": round_money(days_60),
        "debtors_over_90_days": round_money(over_90),
        "debtor_days": round_pct(debtor_days),
        "overdue_invoices_count": overdue_count,
        "overdue_invoices_value": round_money(overdue_value),
        "debtors_health": health,
        "worst_offenders": debtors_totals.get("worst_offenders", []),
    }
