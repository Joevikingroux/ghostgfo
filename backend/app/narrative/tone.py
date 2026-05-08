"""Language / tone configuration per company."""
from __future__ import annotations

LANG_EN = "en"
LANG_AF = "af"

SUPPORTED = {LANG_EN, LANG_AF}


def currency(amount: float) -> str:
    """Format a rand amount for human reading inside narratives."""
    if abs(amount) >= 1_000_000:
        return f"R{amount / 1_000_000:.1f}m"
    if abs(amount) >= 1_000:
        return f"R{amount:,.0f}"
    return f"R{amount:.0f}"


def pct(value: float) -> str:
    return f"{value:+.1f}%".replace("+", "+" if value >= 0 else "")
