"""Cost metrics: total movement + biggest mover detection."""
from __future__ import annotations

from typing import Any

from app.metrics._helpers import round_money, round_pct, safe_pct_change


def compute(income_totals: dict[str, Any]) -> dict[str, Any]:
    current = float(income_totals.get("expenses_current", 0.0)) + float(
        income_totals.get("cost_of_sales_current", 0.0)
    )
    previous = float(income_totals.get("expenses_previous", 0.0)) + float(
        income_totals.get("cost_of_sales_previous", 0.0)
    )

    mover = income_totals.get("top_cost_mover") or {}
    return {
        "total_costs_current": round_money(current),
        "total_costs_previous": round_money(previous),
        "cost_change_pct": round_pct(safe_pct_change(current, previous)),
        "top_cost_mover": mover.get("name"),
        "top_cost_mover_change": round_money(float(mover.get("delta", 0.0))),
        "top_cost_mover_change_pct": round_pct(float(mover.get("delta_pct", 0.0))),
    }
