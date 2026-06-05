"""
CyberRisk360

Purpose:
Process uploaded
security reports.
"""

from app.importers.nessus_pdf_parser import (
    extract_findings
)

from app.services.pdf_importer import (
    parse_pdf_report
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

        print(
            "CONTENT LENGTH:",
            len(pdf_data["content"])
        )

        with open(
            "uploads/live_content.txt",
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                pdf_data["content"]
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