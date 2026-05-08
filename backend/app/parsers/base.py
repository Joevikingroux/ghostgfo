"""Shared parser plumbing for Pastel exports.

Pastel CSV/Excel exports vary by version, locale and report format:

- numbers may be ``"1,234.56"`` or ``"1 234.56"`` or ``"(45,000.00)"``
- header rows may be repeated, blank or shifted down a row or two
- subtotal / "Total" rows are mixed with data rows
- the same column means different things across versions ("Current Month" vs
  "This Period" vs "MTD")
- Excel exports may have multiple junk sheets

This module gives every parser the same toolkit.
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

# ---------------------------------------------------------------------------
# Number normalisation
# ---------------------------------------------------------------------------

_PARENS = re.compile(r"^\s*\((.+)\)\s*$")
_NON_NUMERIC = re.compile(r"[^\d.\-]")


def to_number(value: Any) -> float:
    """Coerce a Pastel-formatted cell into a float.

    Handles: comma thousands, parens-as-negative, currency symbols ('R '),
    NBSP, dashes used as zero, blank cells.
    """
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return 0.0 if pd.isna(value) else float(value)

    text = str(value).strip().replace(" ", " ").replace(" ", "")
    if not text or text in {"-", "—", "–", "nan", "NaN", "None"}:
        return 0.0

    sign = 1.0
    m = _PARENS.match(text)
    if m:
        sign = -1.0
        text = m.group(1)

    text = text.replace("R", "").replace("ZAR", "")
    text = text.replace(",", "")
    text = _NON_NUMERIC.sub("", text)
    if text in {"", "-", "."}:
        return 0.0
    try:
        return sign * float(text)
    except ValueError:
        return 0.0


# ---------------------------------------------------------------------------
# Column name fuzzy matching
# ---------------------------------------------------------------------------


def _slug(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(label).lower())


def find_column(columns: list[str], *aliases: str) -> str | None:
    """Return the actual column name in ``columns`` matching any of ``aliases``.

    Matching is case-insensitive and ignores spaces, hyphens and punctuation,
    so "Current Month", "current_month", "CurrentMonth" and "current-month" all
    match alias ``"current month"``.
    """
    slugged = {_slug(c): c for c in columns}
    for alias in aliases:
        key = _slug(alias)
        if key in slugged:
            return slugged[key]
        for slug, original in slugged.items():
            if key and key in slug:
                return original
    return None


# ---------------------------------------------------------------------------
# File loading
# ---------------------------------------------------------------------------


def load_table(path: str | Path) -> pd.DataFrame:
    """Read a Pastel CSV or Excel export into a DataFrame.

    Skips empty leading rows, picks the first non-empty sheet for Excel, and
    promotes the first non-empty row to header if the loader didn't already.
    """
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix in {".xlsx", ".xls", ".xlsm"}:
        # First non-empty sheet
        all_sheets = pd.read_excel(p, sheet_name=None, header=None, dtype=object)
        sheet_name, raw = next(
            ((n, df) for n, df in all_sheets.items() if not df.dropna(how="all").empty),
            (None, pd.DataFrame()),
        )
        if raw.empty:
            raise ValueError(f"{p}: no non-empty sheet")
        df = _promote_header(raw)
    elif suffix in {".csv", ".txt"}:
        # Pastel sometimes uses ';' or '\t'. Let pandas sniff.
        raw = pd.read_csv(p, header=None, dtype=object, sep=None, engine="python")
        df = _promote_header(raw)
    else:
        raise ValueError(f"{p}: unsupported file type {suffix}")

    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all").reset_index(drop=True)
    return df


def _promote_header(raw: pd.DataFrame) -> pd.DataFrame:
    """Find the first row that looks like headers and promote it."""
    for idx in range(min(10, len(raw))):
        row = raw.iloc[idx]
        non_empty = row.dropna()
        if len(non_empty) >= 2 and all(
            isinstance(v, str) and not _looks_numeric(v) for v in non_empty
        ):
            df = raw.iloc[idx + 1 :].copy()
            df.columns = [
                str(c).strip() if pd.notna(c) else f"col_{i}"
                for i, c in enumerate(raw.iloc[idx])
            ]
            return df.reset_index(drop=True)
    df = raw.copy()
    df.columns = [f"col_{i}" for i in range(len(df.columns))]
    return df


def _looks_numeric(value: str) -> bool:
    try:
        float(str(value).replace(",", "").replace("(", "-").replace(")", ""))
        return True
    except (ValueError, AttributeError):
        return False


# ---------------------------------------------------------------------------
# Subtotal / blank row filtering
# ---------------------------------------------------------------------------

_SUBTOTAL_TOKENS = (
    "total",
    "subtotal",
    "sub total",
    "sub-total",
    "grand total",
    "balance",
    "summary",
)


def is_subtotal_row(label: Any) -> bool:
    if label is None:
        return False
    text = str(label).strip().lower()
    if not text:
        return False
    return any(text.startswith(tok) or text == tok for tok in _SUBTOTAL_TOKENS)


# ---------------------------------------------------------------------------
# Base parser
# ---------------------------------------------------------------------------


@dataclass
class ParseResult:
    """Common envelope for every parser's output."""

    rows: list[dict[str, Any]]
    totals: dict[str, float]
    source_path: str
    warnings: list[str]


class BaseParser(ABC):
    """Subclass per-report. Implement :meth:`parse_dataframe`."""

    name: str = "base"

    def parse(self, path: str | Path) -> ParseResult:
        df = load_table(path)
        warnings: list[str] = []
        rows, totals = self.parse_dataframe(df, warnings)
        return ParseResult(
            rows=rows, totals=totals, source_path=str(path), warnings=warnings
        )

    @abstractmethod
    def parse_dataframe(
        self, df: pd.DataFrame, warnings: list[str]
    ) -> tuple[list[dict[str, Any]], dict[str, float]]:
        """Return (rows, totals)."""
