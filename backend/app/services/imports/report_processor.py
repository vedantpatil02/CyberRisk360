"""
CyberRisk360

Purpose:
Process uploaded
security reports.
"""

from app.importers.nessus_pdf_parser import (
    extract_findings
)

from app.services.imports.pdf_importer import (
    parse_pdf_report
)





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

        return {
            "message":
            "CSV parser coming soon"
        }

    elif file_extension == "nessus":

        return {
            "message":
            "Nessus XML parser coming soon"
        }

    elif file_extension == "pdf":
        # print("PDF DETECTED")

        pdf_data = (
            parse_pdf_report(
                file_path
            )
        )


        # print(
        #     pdf_data["content"][:2000]
        # )

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
                len(pdf_data["content"]),

            "findings_detected":
                len(findings),

            "findings":
                findings,

            "sample":
                findings[:5]
        }
    else:

        return {
            "message":
            "Unsupported file type"
        }