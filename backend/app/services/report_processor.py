"""
CyberRisk360

Purpose:
Process uploaded
security reports.
"""

from app.services.nessus_importer import (
    parse_nessus_csv
)

from app.services.pdf_importer import (
    parse_pdf_report
)

from app.services.nessus_pdf_parser import (
    extract_findings
)

from app.services.nessus_pdf_parser import (
    extract_findings
)

# Future imports
# from app.services.nessus_xml_importer import parse_nessus_xml
# from app.services.pdf_importer import parse_pdf_report


def process_report(
    file_path: str
):
    """
    Detect report type and
    process accordingly.
    """

    file_extension = (
        file_path
        .split(".")[-1]
        .lower()
    )

    if file_extension == "csv":

        findings = (
            parse_nessus_csv(
                file_path
            )
        )

        return {
            "file_type": "csv",
            "findings": len(
                findings
            )
        }

    elif file_extension == "nessus":

        return {
            "message":
            "Nessus XML parser coming soon"
        }

    elif file_extension == "pdf":

        pdf_data = (
            parse_pdf_report(
                file_path
            )
        )

        findings = (
            extract_findings(
                pdf_data["content"]
            )
        )

        return {
            "file_type": "pdf",

            "pages":
                pdf_data["pages"],

            "characters":
                len(
                    pdf_data["content"]
                ),

            "findings_detected":
                len(findings),

            "sample":
                findings[:5]
        }
    else:

        return {
            "message":
            "Unsupported file type"
        }