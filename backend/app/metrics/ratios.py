"""Ratios: gross margin, net margin."""

from __future__ import annotations

from typing import Any

from app.metrics._helpers import round_pct, safe_div


def compute(income_totals: dict[str, Any]) -> dict[str, Any]:
    revenue = float(income_totals.get("revenue_current", 0.0))
    revenue_prev = float(income_totals.get("revenue_previous", 0.0))
    gross = float(income_totals.get("gross_profit_current", 0.0))
    gross_prev = float(income_totals.get("gross_profit_previous", 0.0))

    margin = safe_div(gross, revenue) * 100 if revenue else 0.0
    margin_prev = safe_div(gross_prev, revenue_prev) * 100 if revenue_prev else 0.0

    if abs(margin - margin_prev) < 1.0:
        trend = "stable"
    elif margin > margin_prev:
        trend = "improving"
    else:
        trend = "declining"

    return {
        "gross_profit_current": round(gross, 2),
        "gross_margin_pct": round_pct(margin),
        "gross_margin_prev_pct": round_pct(margin_prev),
        "gross_margin_trend": trend,
    }
