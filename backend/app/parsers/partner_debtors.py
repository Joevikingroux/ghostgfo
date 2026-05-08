"""Pastel Partner Debtor Age Analysis parser.

Expected (loose) columns:
    Customer Code | Customer Name | Current | 30 Days | 60 Days | 90 Days | 90+ Days | Total
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from app.parsers.base import BaseParser, find_column, is_subtotal_row, to_number


class DebtorAgeParser(BaseParser):
    name = "partner_debtors"

    def parse_dataframe(
        self, df: pd.DataFrame, warnings: list[str]
    ) -> tuple[list[dict[str, Any]], dict[str, float]]:
        cols = list(df.columns)

        col_code = find_column(cols, "customer code", "account", "code")
        col_name = find_column(cols, "customer name", "customer", "debtor", "name")
        col_current = find_column(cols, "current", "0-30", "0 to 30", "not yet due")
        col_30 = find_column(cols, "30 days", "31-60", "30-60", "30 to 60", "30")
        col_60 = find_column(cols, "60 days", "61-90", "60-90", "60 to 90", "60")
        col_90 = find_column(cols, "90 days", "90+", "90 +", "over 90", "90 plus", "90")
        col_120 = find_column(cols, "120 days", "120+", "over 120", "120")
        col_total = find_column(cols, "total", "balance", "outstanding")

        if not col_name:
            raise ValueError("Debtor Age: cannot find customer name column")
        if not (col_total or col_current):
            raise ValueError("Debtor Age: cannot find any aging buckets")

        rows: list[dict[str, Any]] = []
        totals = {
            "debtors_current": 0.0,
            "debtors_30_60": 0.0,
            "debtors_61_90": 0.0,
            "debtors_over_90": 0.0,
            "debtors_total": 0.0,
        }
        overdue_invoices: list[dict[str, Any]] = []

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
            d120 = to_number(raw.get(col_120)) if col_120 else 0.0
            row_total = (
                to_number(raw.get(col_total))
                if col_total
                else current + d30 + d60 + d90 + d120
            )

            over_90 = d90 + d120
            customer = {
                "code": str(raw.get(col_code, "") or "").strip() if col_code else "",
                "name": str(name).strip(),
                "current": current,
                "days_30_60": d30,
                "days_61_90": d60,
                "over_90": over_90,
                "total": row_total,
            }
            rows.append(customer)

            totals["debtors_current"] += current
            totals["debtors_30_60"] += d30
            totals["debtors_61_90"] += d60
            totals["debtors_over_90"] += over_90
            totals["debtors_total"] += row_total

            if d60 + over_90 > 0:
                overdue_invoices.append(
                    {
                        "name": customer["name"],
                        "overdue_value": d60 + over_90,
                        "worst_bucket": "90+" if over_90 > 0 else "60-90",
                    }
                )

        overdue_invoices.sort(key=lambda r: r["overdue_value"], reverse=True)
        totals["overdue_invoices_count"] = len(overdue_invoices)
        totals["overdue_invoices_value"] = sum(
            r["overdue_value"] for r in overdue_invoices
        )
        totals["worst_offenders"] = overdue_invoices[:5]  # type: ignore[assignment]

        return rows, totals
