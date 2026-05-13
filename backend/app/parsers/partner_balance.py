"""Pastel Partner Balance Sheet parser.

Expected (loose) columns:
    Account Code | Account Description | Current Balance | Previous Balance

We bucket by code prefix:
    1xxx = assets, 2xxx = liabilities, 3xxx = equity.

Cash = sum of asset accounts whose description matches bank/cash heuristics.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.parsers.base import BaseParser, find_column, is_subtotal_row, to_number

_CASH_HINTS = (
    "bank",
    "cash on hand",
    "petty cash",
    "current account",
    "cheque",
    "savings",
    "fnb",
    "absa",
    "standard bank",
    "nedbank",
    "capitec",
    "investec",
)


def _classify(code: str, desc: str) -> str:
    code = code.strip()
    if code:
        first = code[:1]
        if first == "1":
            return "asset"
        if first == "2":
            return "liability"
        if first == "3":
            return "equity"
    desc_l = desc.lower()
    if "asset" in desc_l:
        return "asset"
    if "liab" in desc_l or "creditor" in desc_l or "loan" in desc_l:
        return "liability"
    if "equity" in desc_l or "retained" in desc_l or "capital" in desc_l:
        return "equity"
    return "other"


def _is_cash_account(desc: str) -> bool:
    d = desc.lower()
    return any(h in d for h in _CASH_HINTS)


class BalanceSheetParser(BaseParser):
    name = "partner_balance"

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
            "current balance",
            "balance",
            "this period",
            "current month",
            "current",
        )
        col_previous = find_column(
            cols, "previous balance", "prior balance", "previous month", "prior"
        )

        if not col_current:
            raise ValueError("Balance Sheet: cannot find current balance column")

        rows: list[dict[str, Any]] = []
        totals = {
            "assets_total": 0.0,
            "liabilities_total": 0.0,
            "equity_total": 0.0,
            "cash_balance": 0.0,
            "cash_balance_previous": 0.0,
        }

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

            kind = _classify(code, desc)
            row = {
                "code": code,
                "description": desc,
                "kind": kind,
                "current": current,
                "previous": previous,
            }
            rows.append(row)

            if kind == "asset":
                totals["assets_total"] += current
                if _is_cash_account(desc):
                    totals["cash_balance"] += current
                    totals["cash_balance_previous"] += previous
            elif kind == "liability":
                totals["liabilities_total"] += abs(current)
            elif kind == "equity":
                totals["equity_total"] += abs(current)

        if not totals["cash_balance"]:
            warnings.append(
                "Balance Sheet: no cash/bank accounts detected — cash runway will be 0."
            )
        return rows, totals
