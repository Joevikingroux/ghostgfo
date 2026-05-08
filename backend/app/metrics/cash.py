"""Cash position, burn rate, runway."""
from __future__ import annotations

from typing import Any

from app.metrics._helpers import round_money, round_pct, safe_div


def compute(
    balance_totals: dict[str, Any],
    monthly_costs: float,
) -> dict[str, Any]:
    cash = float(balance_totals.get("cash_balance", 0.0))
    burn = monthly_costs

    runway_weeks = safe_div(cash, burn) * 4.345 if burn else 0.0  # avg weeks/month
    if runway_weeks < 4:
        health = "critical"
    elif runway_weeks < 12:
        health = "warning"
    else:
        health = "good"

    return {
        "cash_balance": round_money(cash),
        "monthly_burn_rate": round_money(burn),
        "cash_runway_weeks": round_pct(runway_weeks),
        "cash_health": health,
    }
