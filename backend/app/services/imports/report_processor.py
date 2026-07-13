"""
CyberRisk360

Purpose:
Process uploaded
security reports.
"""

from app.importers.nessus_pdf_parser import (
    extract_findings as extract_findings_from_pdf_text
)

from app.importers.nessus_csv_parser import (
    extract_findings as extract_findings_from_csv
)

from app.importers.nessus_xml_parser import (
    extract_findings as extract_findings_from_xml
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

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        findings = extract_findings_from_csv(content)

        return {
            "file_type": "csv",

            "findings_detected":
                len(findings),

            "findings":
                findings,

            "sample":
                findings[:5]
        }

    elif file_extension == "nessus":

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        findings = extract_findings_from_xml(content)

        return {
            "file_type": "nessus",

            "findings_detected":
                len(findings),

            "findings":
                findings,

            "sample":
                findings[:5]
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
            extract_findings_from_pdf_text(
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
