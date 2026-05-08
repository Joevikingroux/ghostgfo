"""Pastel Partner Creditor Age Analysis parser (optional input)."""
from __future__ import annotations

from typing import Any

import pandas as pd

from app.parsers.base import BaseParser, find_column, is_subtotal_row, to_number


class CreditorAgeParser(BaseParser):
    name = "partner_creditors"

    def parse_dataframe(
        self, df: pd.DataFrame, warnings: list[str]
    ) -> tuple[list[dict[str, Any]], dict[str, float]]:
        cols = list(df.columns)

        col_code = find_column(cols, "supplier code", "creditor code", "code")
        col_name = find_column(
            cols, "supplier name", "creditor name", "supplier", "name"
        )
        col_current = find_column(cols, "current", "0-30", "0 to 30")
        col_30 = find_column(cols, "30 days", "31-60", "30-60", "30")
        col_60 = find_column(cols, "60 days", "61-90", "60-90", "60")
        col_90 = find_column(cols, "90 days", "90+", "over 90", "90")
        col_total = find_column(cols, "total", "balance", "outstanding")

        if not col_name:
            raise ValueError("Creditor Age: cannot find supplier name column")

        rows: list[dict[str, Any]] = []
        totals = {
            "creditors_total": 0.0,
            "creditors_current": 0.0,
            "creditors_overdue": 0.0,
        }

        for _, raw in df.iterrows():
            name = raw.get(col_name)
            if pd.isna(name) or str(name).strip() == "":
                continue
            if is_subtotal_row(name):
                continue

            current = to_number(raw.get(col_current)) if col_current else 0.0
            d30 = to_number(raw.get(col_30)) if col_30 else 0.0
            d60 = to_number(raw.get(col_60)) if col_60 else 0.0
            d90 = to_number(raw.get(col_90)) if col_90 else 0.0
            row_total = (
                to_number(raw.get(col_total))
                if col_total
                else current + d30 + d60 + d90
            )

            rows.append(
                {
                    "code": (
                        str(raw.get(col_code, "") or "").strip() if col_code else ""
                    ),
                    "name": str(name).strip(),
                    "current": current,
                    "days_30_60": d30,
                    "days_61_90": d60,
                    "over_90": d90,
                    "total": row_total,
                }
            )

            totals["creditors_total"] += row_total
            totals["creditors_current"] += current
            totals["creditors_overdue"] += d30 + d60 + d90

        return rows, totals
