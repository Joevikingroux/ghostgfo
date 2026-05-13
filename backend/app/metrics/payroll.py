"""Payroll metrics — staff cost, headcount, leave liability, cash cover."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from app.metrics._helpers import round_money, round_pct, safe_div, safe_pct_change


def _next_payroll_date(period_year: int, period_month: int) -> str:
    """Default 25th of the current month, or next month if past."""
    today = date.today()
    target = date(period_year, period_month, 25)
    if target < today:
        # advance one month
        nxt = (target.replace(day=1) + timedelta(days=32)).replace(day=25)
        target = nxt
    return target.isoformat()


def compute(
    summary_totals: dict[str, Any] | None,
    employee_cost_totals: dict[str, Any] | None,
    leave_totals: dict[str, Any] | None,
    *,
    revenue_current: float,
    revenue_previous: float,
    cash_balance: float,
    period_month: int,
    period_year: int,
    previous_payroll_gross: float | None = None,
    previous_headcount: int | None = None,
    journal_integrated: bool = False,
) -> dict[str, Any]:
    summary = summary_totals or {}
    cost = employee_cost_totals or {}
    leave = leave_totals or {}

    gross = float(summary.get("gross_total") or cost.get("gross_total") or 0.0)
    net = float(summary.get("net_total") or 0.0)
    uif_er = float(summary.get("uif_er_total") or cost.get("uif_er_total") or 0.0)
    sdl = float(summary.get("sdl_total") or cost.get("sdl_total") or 0.0)
    true_cost = float(
        summary.get("true_employer_cost")
        or cost.get("true_employer_cost")
        or (gross + uif_er + sdl)
    )
    headcount = int(summary.get("headcount") or 0)
    leave_liability = float(leave.get("leave_liability_rand") or 0.0)

    pct_of_rev = safe_div(true_cost, revenue_current) * 100 if revenue_current else 0.0
    prev_pct = (
        safe_div(previous_payroll_gross or 0.0, revenue_previous) * 100
        if revenue_previous
        else 0.0
    )
    change_pct = (
        safe_pct_change(gross, previous_payroll_gross)
        if previous_payroll_gross is not None
        else 0.0
    )

    weeks_of_payroll = safe_div(leave_liability, gross) * 4.345 if gross else 0.0
    cash_covers = cash_balance >= true_cost * 1.5 if true_cost else True

    if not cash_covers:
        health = "critical"
    elif pct_of_rev > 40 or change_pct > 10 or weeks_of_payroll > 4:
        health = "warning"
    else:
        health = "good"

    return {
        "payroll_gross_total": round_money(gross),
        "payroll_net_total": round_money(net),
        "payroll_employer_uif": round_money(uif_er),
        "payroll_employer_sdl": round_money(sdl),
        "payroll_true_employer_cost": round_money(true_cost),
        "payroll_headcount": headcount,
        "payroll_headcount_change": (headcount - previous_headcount)
        if previous_headcount is not None
        else 0,
        "payroll_pct_of_revenue": round_pct(pct_of_rev),
        "payroll_pct_prev_month": round_pct(prev_pct),
        "payroll_change_pct": round_pct(change_pct),
        "leave_liability_rand": round_money(leave_liability),
        "leave_liability_weeks_payroll": round_pct(weeks_of_payroll),
        "next_payroll_date": _next_payroll_date(period_year, period_month),
        "cash_covers_payroll": cash_covers,
        "payroll_journal_integrated": journal_integrated,
        "payroll_health": health,
    }
