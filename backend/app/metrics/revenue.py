"""Revenue metrics."""
from __future__ import annotations

from typing import Any

from app.metrics._helpers import round_money, round_pct, safe_pct_change


def compute(income_totals: dict[str, Any]) -> dict[str, Any]:
    current = float(income_totals.get("revenue_current", 0.0))
    previous = float(income_totals.get("revenue_previous", 0.0))
    ytd = float(income_totals.get("revenue_ytd", 0.0))

    change_pct = safe_pct_change(current, previous)
    if change_pct >= 5:
        trend = "growing"
    elif change_pct <= -5:
        trend = "declining"
    else:
        trend = "stable"

    return {
        "revenue_current_month": round_money(current),
        "revenue_previous_month": round_money(previous),
        "revenue_change_pct": round_pct(change_pct),
        "revenue_ytd": round_money(ytd),
        "revenue_trend": trend,
    }
