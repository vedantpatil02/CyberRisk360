"""
CyberRisk360

Purpose:
Extract findings from
Nessus PDF reports.
"""

import re

FINDING_PATTERN = re.compile(
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

# A line that is nothing but a host IP - marks the start of that
# host's block of findings in the "Vulnerabilities by Host" section.
HOST_HEADER_PATTERN = re.compile(r"^(\d+\.\d+\.\d+\.\d+)$")

# The per-page footer Nessus repeats on every page ("<ip> <page>"),
# which pypdf's text extraction sometimes glues directly onto the
# start of the next finding line with no newline in between (e.g.
# "192.168.0.169 4LOW 2.6* - - 71049 SSH Weak MAC Algorithms Enabled").
HOST_FOOTER_PATTERN = re.compile(r"^(\d+\.\d+\.\d+\.\d+)\s+\d+\s*(.*)$")


def _build_finding(match, ip_address):
    return {
        "ip_address": ip_address,
        "severity": match.group(1),
        "cvss_score": float(match.group(2).replace("*", "")),
        "plugin_id": match.group(3),
        "title": match.group(4)
    }


def extract_findings(
    content: str
):
    """
    Extract findings, tracking the current host as a running state
    rather than a single document-wide first IP match - a report
    covering multiple hosts has one "Vulnerabilities by Host" block
    per host, each starting with its own IP header line, and every
    finding must be attributed to the host whose block it actually
    appears in, not whichever IP happens to appear first in the PDF.
    """

    findings = []
    current_ip = "Unknown"

    for line in content.splitlines():

        stripped = line.strip()

        header_match = HOST_HEADER_PATTERN.match(stripped)

        if header_match:
            current_ip = header_match.group(1)
            continue

        footer_match = HOST_FOOTER_PATTERN.match(stripped)

        if footer_match:
            current_ip = footer_match.group(1)
            stripped = footer_match.group(2).strip()

        finding_match = FINDING_PATTERN.match(stripped)

        if not finding_match:
            continue

        findings.append(
            _build_finding(finding_match, current_ip)
        )

    return findings