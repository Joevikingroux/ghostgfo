"""WeasyPrint PDF generator.

Renders the Jinja2 HTML template to a PDF file and returns its path.
"""

from __future__ import annotations

import calendar
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from app.core.config import settings
from app.core.logging import get_logger
from app.narrative.generator import Narrative

log = get_logger(__name__)

_TEMPLATES_DIR = Path(__file__).parent / "templates"

_jinja = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=True,
)


# Register custom filters
def _currency(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"R {value / 1_000_000:.2f}m"
    return f"R {value:,.0f}"


def _pct_class(value: float) -> str:
    """Return a CSS class name for colouring a percentage."""
    if value < 0:
        return "neg"
    if value > 0:
        return "pos"
    return "neutral"


def _health_class(rating: str) -> str:
    return {
        "excellent": "health-excellent",
        "good": "health-good",
        "fair": "health-fair",
        "poor": "health-poor",
        "critical": "health-critical",
    }.get(rating, "health-fair")


_jinja.filters["currency"] = _currency
_jinja.filters["pct_class"] = _pct_class
_jinja.filters["health_class"] = _health_class


def generate_pdf(
    metrics: dict[str, Any],
    narrative: Narrative,
    output_dir: Path | None = None,
) -> Path:
    """Render the report to a PDF file and return its path."""
    month = metrics["period_month"]
    year = metrics["period_year"]
    company_slug = (
        metrics.get("company_name", "report")
        .lower()
        .replace(" ", "_")
        .replace("/", "_")[:40]
    )

    out_dir = output_dir or settings.reports_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{company_slug}_{year}-{month:02d}.pdf"

    css_path = _TEMPLATES_DIR / "styles.css"
    # WeasyPrint resolves relative hrefs against base_url; pass an absolute file URI
    styles_url = css_path.as_uri()

    template = _jinja.get_template("monthly_report.html")
    html_str = template.render(
        metrics=metrics,
        narrative=narrative,
        month_name=calendar.month_name[month],
        brand_primary=settings.brand_primary,
        brand_secondary=settings.brand_secondary,
        brand_footer=settings.brand_footer,
        styles_url=styles_url,
        lang=metrics.get("language", "en"),
        ai_generated=getattr(narrative, "ai_generated", False),
    )

    HTML(string=html_str, base_url=str(_TEMPLATES_DIR)).write_pdf(str(out_path))

    # Encrypt at rest — replace plaintext PDF with AES-256-GCM blob
    from app.core.pdf_crypto import encrypt_pdf
    enc_path = Path(str(out_path) + ".enc")
    enc_path.write_bytes(encrypt_pdf(out_path.read_bytes()))
    out_path.unlink()
    out_path = enc_path

    log.info(
        "pdf.generated", path=str(out_path), size_kb=out_path.stat().st_size // 1024
    )
    return out_path
