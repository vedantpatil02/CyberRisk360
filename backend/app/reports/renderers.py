"""
CyberRisk360

Purpose:
Render structured report data into deliverable formats.

HTML is produced with Jinja2 (autoescaping ON - reports embed
user-controlled vulnerability text, so escaping is a security control,
not a nicety). PDF is produced from that HTML with xhtml2pdf, which is
pure-Python (no system libraries), so it works inside the app container
without extra OS packages.
"""

import io
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from xhtml2pdf import pisa


TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

# Maps a report's `report_type` to its template file. Keeps the API and
# builders decoupled from template filenames.
TEMPLATE_BY_REPORT_TYPE = {
    "Executive Summary": "executive.html",
    "Technical Vulnerability Report": "technical.html",
    "Compliance Assessment Report": "compliance.html",
}


_environment = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


class ReportRenderError(Exception):
    """
    Raised when a report cannot be rendered (unknown type, or the PDF
    engine reported an error).
    """


def render_html(report: dict) -> str:
    """
    Render a report dict to an HTML string.
    """

    template_name = TEMPLATE_BY_REPORT_TYPE.get(
        report.get("report_type")
    )

    if template_name is None:
        raise ReportRenderError(
            f"No template for report type: {report.get('report_type')}"
        )

    template = _environment.get_template(template_name)

    return template.render(report=report, sections=report["sections"])


def render_pdf(report: dict) -> bytes:
    """
    Render a report dict to PDF bytes (via its HTML rendering).
    """

    html = render_html(report)

    buffer = io.BytesIO()

    result = pisa.CreatePDF(src=html, dest=buffer)

    if result.err:
        raise ReportRenderError("PDF generation failed")

    return buffer.getvalue()
