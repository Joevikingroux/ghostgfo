"""Pastel Payroll — Employee Cost Report parser.

Per-employee row:
    Employee Code | Employee Name | Basic Salary | Overtime | Bonus |
    Total Gross | Employer UIF | Employer SDL | Total Employer Cost
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from app.parsers.base import BaseParser, find_column, is_subtotal_row, to_number


class EmployeeCostParser(BaseParser):
    name = "payroll_employee_cost"

    def parse_dataframe(
        self, df: pd.DataFrame, warnings: list[str]
    ) -> tuple[list[dict[str, Any]], dict[str, float]]:
        cols = list(df.columns)

        col_code = find_column(cols, "employee code", "emp code", "code")
        col_name = find_column(cols, "employee name", "employee", "name")
        col_basic = find_column(cols, "basic salary", "basic", "salary")
        col_overtime = find_column(cols, "overtime", "ot")
        col_bonus = find_column(cols, "bonus", "commission", "incentive")
        col_gross = find_column(cols, "total gross", "gross", "total earnings")
        col_uif_er = find_column(
            cols, "employer uif", "uif (er)", "uif er", "uif employer"
        )
        col_sdl = find_column(cols, "employer sdl", "sdl", "skills levy")
        col_total = find_column(
            cols, "total employer cost", "employer cost", "total cost", "ctc"
        )

        if not col_name:
            raise ValueError("Employee Cost: cannot find employee name column")

        rows: list[dict[str, Any]] = []
        totals = {
            "basic_total": 0.0,
            "overtime_total": 0.0,
            "bonus_total": 0.0,
            "gross_total": 0.0,
            "uif_er_total": 0.0,
            "sdl_total": 0.0,
            "true_employer_cost": 0.0,
        }

        for _, raw in df.iterrows():
            name = raw.get(col_name)
            if pd.isna(name) or str(name).strip() == "":
                continue
            if is_subtotal_row(name):
                continue

            basic = to_number(raw.get(col_basic)) if col_basic else 0.0
            overtime = to_number(raw.get(col_overtime)) if col_overtime else 0.0
            bonus = to_number(raw.get(col_bonus)) if col_bonus else 0.0
            gross = (
                to_number(raw.get(col_gross))
                if col_gross
                else basic + overtime + bonus
            )
            uif_er = to_number(raw.get(col_uif_er)) if col_uif_er else gross * 0.01
            sdl = to_number(raw.get(col_sdl)) if col_sdl else gross * 0.01
            total_cost = (
                to_number(raw.get(col_total))
                if col_total
                else gross + uif_er + sdl
            )

            row = {
                "code": str(raw.get(col_code, "") or "").strip() if col_code else "",
                "name": str(name).strip(),
                "basic": basic,
                "overtime": overtime,
                "bonus": bonus,
                "gross": gross,
                "uif_er": uif_er,
                "sdl": sdl,
                "total_employer_cost": total_cost,
            }
            rows.append(row)

            totals["basic_total"] += basic
            totals["overtime_total"] += overtime
            totals["bonus_total"] += bonus
            totals["gross_total"] += gross
            totals["uif_er_total"] += uif_er
            totals["sdl_total"] += sdl
            totals["true_employer_cost"] += total_cost

        if not rows:
            warnings.append("Employee Cost: no employee rows found")
        return rows, totals
