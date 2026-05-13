"""Pastel Partner Income Statement parser.

Expected (loose) columns:
    Account Code | Account Description | Current Month | Previous Month | YTD | Budget

Pastel Partner classifies accounts via the Account Code prefix:
    1xxx = assets, 2xxx = liabilities, 3xxx = equity,
    4xxx = income, 5xxx = cost of sales, 6xxx-9xxx = expenses

We do not assume that every export carries a "type" column — most don't.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.parsers.base import BaseParser, find_column, is_subtotal_row, to_number


def classify_account(code: str | None, description: str | None) -> str:
    """Return one of: revenue | cost_of_sales | expense | other."""
    code_str = str(code or "").strip()
    desc = (description or "").lower()

    # Code-based (Pastel default chart)
    if code_str:
        first = code_str[0]
        if first == "4":
            return "revenue"
        if first == "5":
            return "cost_of_sales"
        if first in {"6", "7", "8", "9"}:
            return "expense"

    # Fallback: description keywords
    if any(k in desc for k in ("sales", "revenue", "income", "turnover")):
        return "revenue"
    if any(k in desc for k in ("cost of sales", "cogs", "purchases", "stock")):
        return "cost_of_sales"
    if any(
        k in desc
        for k in (
            "salar",
            "wage",
            "rent",
            "expense",
            "fee",
            "telephone",
            "fuel",
            "repair",
            "insurance",
            "uif",
            "sdl",
            "paye",
            "bank charge",
        )
    ):
        return "expense"
    return "other"


class IncomeStatementParser(BaseParser):
    name = "partner_income"

    def parse_dataframe(
        self, df: pd.DataFrame, warnings: list[str]
    ) -> tuple[list[dict[str, Any]], dict[str, float]]:
        cols = list(df.columns)

        col_code = find_column(cols, "account code", "code", "gl code")
        col_desc = find_column(
            cols, "account description", "description", "account name", "name"
        )
        col_current = find_column(
            cols,
            "current month",
            "this period",
            "this month",
            "actual current",
            "mtd",
            "current",
        )
        col_previous = find_column(
            cols, "previous month", "prior month", "last month", "prior period"
        )
        col_ytd = find_column(cols, "ytd", "year to date", "year-to-date")
        col_budget = find_column(cols, "budget", "budget current month", "budget mtd")

        if not col_desc and not col_code:
            raise ValueError(
                "Income Statement: cannot find Account Code or Description column"
            )
        if not col_current:
            raise ValueError("Income Statement: cannot find Current Month column")

        rows: list[dict[str, Any]] = []
        totals = {
            "revenue_current": 0.0,
            "revenue_previous": 0.0,
            "revenue_ytd": 0.0,
            "cost_of_sales_current": 0.0,
            "cost_of_sales_previous": 0.0,
            "expenses_current": 0.0,
            "expenses_previous": 0.0,
            "expenses_ytd": 0.0,
        }
        cost_movers: dict[str, dict[str, float]] = {}

        for _, raw in df.iterrows():
            label = raw.get(col_desc) if col_desc else raw.get(col_code)
            if pd.isna(label) or str(label).strip() == "":
                continue
            if is_subtotal_row(label):
                continue

            code = str(raw.get(col_code, "") or "").strip() if col_code else ""
            desc = str(raw.get(col_desc, "") or "").strip() if col_desc else code
            current = to_number(raw.get(col_current))
            previous = to_number(raw.get(col_previous)) if col_previous else 0.0
            ytd = to_number(raw.get(col_ytd)) if col_ytd else current
            budget = to_number(raw.get(col_budget)) if col_budget else 0.0

            kind = classify_account(code, desc)

            if kind == "revenue":
                # Pastel often stores income as negatives in TB-style exports.
                current_norm = abs(current)
                previous_norm = abs(previous)
                ytd_norm = abs(ytd)
                totals["revenue_current"] += current_norm
                totals["revenue_previous"] += previous_norm
                totals["revenue_ytd"] += ytd_norm
                rows.append(
                    {
                        "code": code,
                        "description": desc,
                        "kind": kind,
                        "current": current_norm,
                        "previous": previous_norm,
                        "ytd": ytd_norm,
                        "budget": abs(budget),
                    }
                )
                continue

            current_norm = abs(current)
            previous_norm = abs(previous)
            ytd_norm = abs(ytd)
            if kind == "cost_of_sales":
                totals["cost_of_sales_current"] += current_norm
                totals["cost_of_sales_previous"] += previous_norm
            elif kind == "expense":
                totals["expenses_current"] += current_norm
                totals["expenses_previous"] += previous_norm
                totals["expenses_ytd"] += ytd_norm
                cost_movers[desc] = {
                    "current": current_norm,
                    "previous": previous_norm,
                    "delta": current_norm - previous_norm,
                }
            rows.append(
                {
                    "code": code,
                    "description": desc,
                    "kind": kind,
                    "current": current_norm,
                    "previous": previous_norm,
                    "ytd": ytd_norm,
                    "budget": abs(budget),
                }
            )

        # Top mover by absolute change (only meaningful for expenses)
        top_mover = None
        if cost_movers:
            top_mover_name, top = max(
                cost_movers.items(), key=lambda kv: abs(kv[1]["delta"])
            )
            top_mover = {
                "name": top_mover_name,
                "current": top["current"],
                "previous": top["previous"],
                "delta": top["delta"],
                "delta_pct": (
                    (top["delta"] / top["previous"] * 100) if top["previous"] else 0.0
                ),
            }
        totals["top_cost_mover"] = top_mover  # type: ignore[assignment]
        totals["gross_profit_current"] = (
            totals["revenue_current"] - totals["cost_of_sales_current"]
        )
        totals["gross_profit_previous"] = (
            totals["revenue_previous"] - totals["cost_of_sales_previous"]
        )

        if not totals["revenue_current"]:
            warnings.append(
                "Income Statement: no revenue rows detected — check Account Code prefixes."
            )

        return rows, totals
