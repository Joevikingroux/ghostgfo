"""Pastel Payroll — Leave Liability Report parser.

Per-employee row:
    Employee Code | Employee Name | Leave Type | Balance Days |
    Daily Rate | Liability (Rand)
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from app.parsers.base import BaseParser, find_column, is_subtotal_row, to_number


class LeaveLiabilityParser(BaseParser):
    name = "payroll_leave"

    def parse_dataframe(
        self, df: pd.DataFrame, warnings: list[str]
    ) -> tuple[list[dict[str, Any]], dict[str, float]]:
        cols = list(df.columns)

        col_code = find_column(cols, "employee code", "emp code", "code")
        col_name = find_column(cols, "employee name", "employee", "name")
        col_type = find_column(cols, "leave type", "type")
        col_days = find_column(
            cols, "balance days", "balance", "days outstanding", "days"
        )
        col_rate = find_column(cols, "daily rate", "rate per day", "rate")
        col_liability = find_column(
            cols, "liability (rand)", "liability rand", "liability", "rand value"
        )

        if not col_name:
            raise ValueError("Leave Liability: cannot find employee name column")

        rows: list[dict[str, Any]] = []
        totals = {
            "leave_liability_rand": 0.0,
            "leave_balance_days_total": 0.0,
        }

        for _, raw in df.iterrows():
            name = raw.get(col_name)
            if pd.isna(name) or str(name).strip() == "":
                continue
            if is_subtotal_row(name):
                continue

            leave_type = (
                str(raw.get(col_type, "") or "").strip().lower() if col_type else ""
            )
            # Only annual leave is a real cash liability
            if leave_type and "annual" not in leave_type and "leave" != leave_type:
                continue

            days = to_number(raw.get(col_days)) if col_days else 0.0
            rate = to_number(raw.get(col_rate)) if col_rate else 0.0
            liability = (
                to_number(raw.get(col_liability))
                if col_liability
                else days * rate
            )

            rows.append(
                {
                    "code": (
                        str(raw.get(col_code, "") or "").strip() if col_code else ""
                    ),
                    "name": str(name).strip(),
                    "leave_type": leave_type or "annual",
                    "balance_days": days,
                    "daily_rate": rate,
                    "liability": liability,
                }
            )

            totals["leave_liability_rand"] += liability
            totals["leave_balance_days_total"] += days

        return rows, totals
