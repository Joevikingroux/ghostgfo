"""Pull financial data from Pastel Evolution and normalise it into the
backend-compatible JSON payload shape.

The extractor tries each query independently so a missing linked Payroll DB
(PAYROLL_SUMMARY, LEAVE_LIABILITY) won't abort the whole run — it just omits
those fields.
"""
from __future__ import annotations

import datetime
from typing import Any

from connector import queries, evolution_db


def _safe_query(conn: Any, sql: str, label: str) -> list[dict[str, Any]]:
    try:
        return evolution_db.run_query(conn, sql)
    except Exception as exc:
        print(f"  [WARN] {label} query failed: {exc}")
        return []


def _latest_two_periods(
    rows: list[dict[str, Any]], date_key: str
) -> tuple[list[dict], list[dict]]:
    """Split rows into current-period and previous-period buckets."""
    if not rows:
        return [], []
    dates = sorted({r[date_key] for r in rows if r.get(date_key)}, reverse=True)
    if len(dates) < 2:
        current_rows = [r for r in rows if r.get(date_key) == dates[0]]
        return current_rows, []
    current_rows = [r for r in rows if r.get(date_key) == dates[0]]
    prev_rows = [r for r in rows if r.get(date_key) == dates[1]]
    return current_rows, prev_rows


def _sum_field(rows: list[dict], field: str) -> float:
    return sum(float(r.get(field) or 0) for r in rows)


def extract(conn: Any) -> dict[str, Any]:
    """Run all queries and return the normalised payload dict."""
    now = datetime.datetime.utcnow()
    period_date = now.replace(day=1) - datetime.timedelta(days=1)  # last day of prev month
    period_month = period_date.month
    period_year = period_date.year

    # --- Revenue ---
    rev_rows = _safe_query(conn, queries.REVENUE_MONTHLY, "revenue")
    curr_rev, prev_rev = _latest_two_periods(rev_rows, "period_date")
    revenue_current = abs(_sum_field(curr_rev, "total_revenue"))
    revenue_previous = abs(_sum_field(prev_rev, "total_revenue"))
    revenue_ytd = abs(sum(float(r.get("total_revenue") or 0) for r in rev_rows
                         if r.get("period_date") and r["period_date"].year == period_year))

    # --- Cost of sales ---
    cos_rows = _safe_query(conn, queries.COST_OF_SALES_MONTHLY, "cost_of_sales")
    curr_cos, prev_cos = _latest_two_periods(cos_rows, "period_date")
    cos_current = abs(_sum_field(curr_cos, "total_cos"))
    cos_previous = abs(_sum_field(prev_cos, "total_cos"))

    # --- Expenses ---
    exp_rows = _safe_query(conn, queries.EXPENSES_MONTHLY, "expenses")
    curr_exp = [r for r in exp_rows if r.get("period_date") and
                r["period_date"] >= period_date.replace(day=1)]
    prev_exp = [r for r in exp_rows if r.get("period_date") and
                r["period_date"] < period_date.replace(day=1)]
    expenses_current = abs(_sum_field(curr_exp, "amount"))
    expenses_previous = abs(_sum_field(prev_exp, "amount"))

    # Top cost mover
    exp_by_account: dict[str, dict] = {}
    for r in curr_exp:
        name = r["account_name"]
        curr_amt = abs(float(r.get("amount") or 0))
        prev_amt = abs(float(
            next((x.get("amount", 0) for x in prev_exp if x["account_name"] == name), 0) or 0
        ))
        exp_by_account[name] = {
            "name": name, "current": curr_amt, "previous": prev_amt,
            "delta": curr_amt - prev_amt,
            "delta_pct": ((curr_amt - prev_amt) / prev_amt * 100) if prev_amt else 0.0,
        }
    top_mover = max(exp_by_account.values(), key=lambda v: abs(v["delta"]), default=None)

    # --- Debtors ---
    deb_rows = _safe_query(conn, queries.DEBTOR_AGE, "debtors")
    debtors_current = _sum_field(deb_rows, "current_amount")
    debtors_30_60 = _sum_field(deb_rows, "days_30_60")
    debtors_61_90 = _sum_field(deb_rows, "days_61_90")
    debtors_over_90 = _sum_field(deb_rows, "over_90_days")
    debtors_total = _sum_field(deb_rows, "total_outstanding")
    overdue_rows = [r for r in deb_rows if (float(r.get("days_61_90") or 0) +
                                             float(r.get("over_90_days") or 0)) > 0]
    worst_offenders = [
        {
            "name": r["customer_name"],
            "overdue_value": float(r.get("days_61_90") or 0) + float(r.get("over_90_days") or 0),
            "worst_bucket": "90+" if float(r.get("over_90_days") or 0) > 0 else "61-90",
        }
        for r in sorted(overdue_rows,
                        key=lambda x: float(x.get("over_90_days") or 0) + float(x.get("days_61_90") or 0),
                        reverse=True)[:5]
    ]

    # --- Creditors ---
    cred_rows = _safe_query(conn, queries.CREDITOR_AGE, "creditors")
    creditors_total = _sum_field(cred_rows, "total_outstanding")
    creditors_current = _sum_field(cred_rows, "current_amount")
    creditors_overdue = (_sum_field(cred_rows, "days_30_60") +
                         _sum_field(cred_rows, "days_61_90") +
                         _sum_field(cred_rows, "over_90_days"))

    # --- Cash ---
    cash_rows = _safe_query(conn, queries.CASH_BALANCE, "cash")
    cash_balance = sum(float(r.get("balance") or 0) for r in cash_rows)

    # --- Payroll GL journal detection ---
    journal_rows = _safe_query(conn, queries.PAYROLL_JOURNAL_CHECK, "payroll_journal")
    payroll_journal_integrated = len(journal_rows) > 0

    # --- Payroll (linked DB, optional) ---
    payroll_summary: dict[str, Any] = {}
    leave_totals: dict[str, Any] = {}
    pay_rows = _safe_query(conn, queries.PAYROLL_SUMMARY, "payroll_summary")
    if pay_rows:
        # Most recent period
        latest_pay = sorted(pay_rows, key=lambda r: r.get("period_end") or datetime.date.min, reverse=True)[0]
        gross = float(latest_pay.get("gross_payroll") or 0)
        uif_er = float(latest_pay.get("employer_uif") or 0)
        sdl = float(latest_pay.get("employer_sdl") or 0)
        payroll_summary = {
            "headcount": int(latest_pay.get("headcount") or 0),
            "gross_total": gross,
            "uif_er_total": uif_er,
            "sdl_total": sdl,
            "net_total": float(latest_pay.get("net_payroll") or 0),
            "true_employer_cost": gross + uif_er + sdl,
        }

    leave_rows = _safe_query(conn, queries.LEAVE_LIABILITY, "leave_liability")
    if leave_rows:
        leave_totals = {
            "leave_liability_rand": sum(float(r.get("liability_rand") or 0) for r in leave_rows),
            "leave_balance_days_total": sum(float(r.get("balance_days") or 0) for r in leave_rows),
        }

    return {
        "period_month": period_month,
        "period_year": period_year,
        "extracted_at": now.isoformat(),
        "income_totals": {
            "revenue_current": revenue_current,
            "revenue_previous": revenue_previous,
            "revenue_ytd": revenue_ytd,
            "cost_of_sales_current": cos_current,
            "cost_of_sales_previous": cos_previous,
            "expenses_current": expenses_current,
            "expenses_previous": expenses_previous,
            "expenses_ytd": expenses_current,
            "gross_profit_current": revenue_current - cos_current,
            "gross_profit_previous": revenue_previous - cos_previous,
            "top_cost_mover": top_mover,
        },
        "balance_totals": {
            "cash_balance": cash_balance,
            "cash_balance_previous": 0.0,
            "assets_total": 0.0,
            "liabilities_total": 0.0,
            "equity_total": 0.0,
        },
        "debtors_totals": {
            "debtors_current": debtors_current,
            "debtors_30_60": debtors_30_60,
            "debtors_61_90": debtors_61_90,
            "debtors_over_90": debtors_over_90,
            "debtors_total": debtors_total,
            "overdue_invoices_count": len(overdue_rows),
            "overdue_invoices_value": sum(r["overdue_value"] for r in worst_offenders),
            "worst_offenders": worst_offenders,
        },
        "creditors_totals": {
            "creditors_total": creditors_total,
            "creditors_current": creditors_current,
            "creditors_overdue": creditors_overdue,
        },
        "payroll_summary_totals": payroll_summary or None,
        "payroll_employee_cost_totals": None,
        "payroll_leave_totals": leave_totals or None,
        "payroll_journal_integrated": payroll_journal_integrated,
    }
