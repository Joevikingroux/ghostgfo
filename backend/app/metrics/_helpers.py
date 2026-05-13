"""Small helpers shared across metric calculators."""

from __future__ import annotations


def safe_pct_change(current: float, previous: float) -> float:
    """Percent change, robust to zero or near-zero previous values."""
    if previous == 0:
        return 0.0 if current == 0 else 100.0 if current > 0 else -100.0
    return (current - previous) / abs(previous) * 100


def safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    if denominator == 0:
        return default
    return numerator / denominator


def round_money(value: float) -> float:
    return round(value, 2)


def round_pct(value: float) -> float:
    return round(value, 1)
