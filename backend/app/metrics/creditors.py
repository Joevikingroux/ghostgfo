"""Creditor metrics (optional input)."""

from __future__ import annotations

from typing import Any

from app.metrics._helpers import round_money, round_pct, safe_div


def compute(creditors_totals: dict[str, Any], costs_current: float) -> dict[str, Any]:
    total = float(creditors_totals.get("creditors_total", 0.0))
    overdue = float(creditors_totals.get("creditors_overdue", 0.0))
    creditor_days = safe_div(total, costs_current) * 30 if costs_current else 0.0
    return {
        "creditors_total": round_money(total),
        "creditors_overdue": round_money(overdue),
        "creditor_days": round_pct(creditor_days),
        "top_creditors": creditors_totals.get("top_creditors", []),
    }
