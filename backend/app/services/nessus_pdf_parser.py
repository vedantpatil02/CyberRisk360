"""
CyberRisk360

Purpose:
Extract findings from
Nessus PDF reports.
"""

import re


def extract_findings(
    content: str
):
    """
    Extract potential findings.
    """

    findings = []

    severity_pattern = (
        r"(Critical|High|Medium|Low)"
    )

    matches = re.finditer(
        severity_pattern,
        content,
        re.IGNORECASE
    )

    for match in matches:

        findings.append(
            {
                "severity":
                match.group()
            }
        )

    return findings