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
    Extract findings from
    Nessus PDF text.
    """

    findings = []

    pattern = (
        r'(\d+\.\d+\.\d+\.\d+)'
        r'.*?'
        r'(CVE-\d{4}-\d+)'
        r'\s+'
        r'(\d+\.\d+)'
        r'\s+'
        r'(CRITICAL|HIGH|MEDIUM|LOW)'
    )

    matches = re.finditer(
        pattern,
        content,
        re.IGNORECASE | re.DOTALL
    )

    for match in matches:

        findings.append(
            {
                "ip_address":
                    match.group(1),

                "cve_id":
                    match.group(2),

                "cvss_score":
                    float(
                        match.group(3)
                    ),

                "severity":
                    match.group(4)
            }
        )

    return findings