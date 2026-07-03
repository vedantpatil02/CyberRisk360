"""
CyberRisk360

Purpose:
Extract text from PDF reports.
"""

from pypdf import PdfReader


def parse_pdf_report(
    file_path: str
):
    """
    Extract text from PDF.
    """

    reader = PdfReader(
        file_path
    )

    content = ""

    for page in reader.pages:

        text = page.extract_text()

        if text:

            content += text

    return {
        "pages": len(
            reader.pages
        ),
        "content": content
    }