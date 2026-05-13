"""Pastel Payroll — Payroll Summary export parser.

Per-employee row:
    Employee Code | Employee Name | Department | Gross Pay | PAYE |
    UIF (EE) | UIF (ER) | SDL | Other Deductions | Net Pay
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.parsers.base import BaseParser, find_column, is_subtotal_row, to_number


class PayrollSummaryParser(BaseParser):
    name = "payroll_summary"

    def parse_dataframe(
        self, df: pd.DataFrame, warnings: list[str]
    ) -> tuple[list[dict[str, Any]], dict[str, float]]:
        cols = list(df.columns)

        col_code = find_column(cols, "employee code", "emp code", "code", "id")
        col_name = find_column(cols, "employee name", "employee", "name", "full name")
        col_dept = find_column(cols, "department", "dept", "cost centre", "branch")
        col_gross = find_column(
            cols, "gross pay", "gross", "total earnings", "earnings"
        )
        col_paye = find_column(cols, "paye", "tax", "income tax")
        col_uif_ee = find_column(cols, "uif ee", "uif (ee)", "uif employee", "uif")
        col_uif_er = find_column(cols, "uif er", "uif (er)", "uif employer")
        col_sdl = find_column(cols, "sdl", "skills levy", "sdl levy")
        col_deductions = find_column(
            cols, "other deductions", "deductions", "total deductions"
        )
        col_net = find_column(cols, "net pay", "net", "take home", "nett")

        if not col_name:
            raise ValueError("Payroll Summary: cannot find employee name column")
        if not col_gross:
            raise ValueError("Payroll Summary: cannot find gross pay column")

        rows: list[dict[str, Any]] = []
        totals = {
            "headcount": 0,
            "gross_total": 0.0,
            "paye_total": 0.0,
            "uif_ee_total": 0.0,
            "uif_er_total": 0.0,
            "sdl_total": 0.0,
            "other_deductions_total": 0.0,
            "net_total": 0.0,
        }

        for _, raw in df.iterrows():
            name = raw.get(col_name)
            if pd.isna(name) or str(name).strip() == "":
                continue
            if is_subtotal_row(name):
                continue
            # Department subtotals often have empty employee code + populated department only
            dept_value = raw.get(col_dept) if col_dept else None
            code_value = raw.get(col_code) if col_code else None
            if (
                col_dept
                and dept_value
                and not pd.isna(dept_value)
                and (code_value is None or pd.isna(code_value))
                and is_subtotal_row(name)
            ):
                continue

            gross = to_number(raw.get(col_gross))
            paye = to_number(raw.get(col_paye)) if col_paye else 0.0
            uif_ee = to_number(raw.get(col_uif_ee)) if col_uif_ee else 0.0
            uif_er = to_number(raw.get(col_uif_er)) if col_uif_er else gross * 0.01
            sdl = to_number(raw.get(col_sdl)) if col_sdl else gross * 0.01
            other = to_number(raw.get(col_deductions)) if col_deductions else 0.0
            net = (
                to_number(raw.get(col_net))
                if col_net
                else gross - paye - uif_ee - other
            )

            row = {
                "code": str(code_value or "").strip(),
                "name": str(name).strip(),
                "department": str(dept_value or "").strip()
                if dept_value and not pd.isna(dept_value)
                else "",
                "gross": gross,
                "paye": paye,
                "uif_ee": uif_ee,
                "uif_er": uif_er,
                "sdl": sdl,
                "other_deductions": other,
                "net": net,
            }
            rows.append(row)

            totals["headcount"] += 1
            totals["gross_total"] += gross
            totals["paye_total"] += paye
            totals["uif_ee_total"] += uif_ee
            totals["uif_er_total"] += uif_er
            totals["sdl_total"] += sdl
            totals["other_deductions_total"] += other
            totals["net_total"] += net

        totals["true_employer_cost"] = (
            totals["gross_total"] + totals["uif_er_total"] + totals["sdl_total"]
        )

        if not rows:
            warnings.append("Payroll Summary: no employee rows found")

        return rows, totals
