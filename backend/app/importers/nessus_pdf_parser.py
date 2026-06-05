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

    findings = []

    ip_match = re.search(
        r"\d+\.\d+\.\d+\.\d+",
        content
    )

    ip_address = (
        ip_match.group()
        if ip_match
        else "Unknown"
    )

    pattern = (
        r"(CRITICAL|HIGH|MEDIUM|LOW)"
        r"\s+"
        r"(\d+(?:\.\d+)?\*?)"
        r"\s+"
        r"[\d\.-]+"
        r"\s+"
        r"[\d\.-]+"
        r"\s+"
        r"(\d+)"
        r"\s+"
        r"(.+)"
    )

    for line in content.splitlines():

        match = re.match(
            pattern,
            line.strip()
        )

        if not match:
            continue

        findings.append(
            {
                "ip_address":
                    ip_address,

                "severity":
                    match.group(1),

                "cvss_score":
                    float(
                        match.group(2)
                        .replace("*", "")
                    ),

                "plugin_id":
                    match.group(3),

                "title":
                    match.group(4)
            }
        )

    return findings