"""
CyberRisk360

Purpose:
Extract findings from Nessus CSV report exports.
"""

import csv
import io

# Nessus's real CSV export uses "None" for informational rows - skipped,
# matching the PDF parser's existing behavior of silently ignoring
# INFO-level findings (its regex never matches them either).
_SKIPPED_RISK_LEVELS = {"NONE", ""}


def extract_findings(
    content: str
):
    """
    Parse a Nessus CSV export (columns: Plugin ID, CVE, CVSS, Risk,
    Host, Protocol, Port, Name, Synopsis, Description, Solution,
    See Also, Plugin Output) into the same finding dict shape the PDF
    and .nessus XML parsers produce.
    """

    findings = []

    reader = csv.DictReader(io.StringIO(content))

    for row in reader:

        risk = (row.get("Risk") or "").strip().upper()

        if risk in _SKIPPED_RISK_LEVELS:
            continue

        plugin_id = (row.get("Plugin ID") or "").strip()
        cvss_raw = (row.get("CVSS") or "").strip()
        host = (row.get("Host") or "").strip()
        name = (row.get("Name") or "").strip()

        if not plugin_id or not cvss_raw:
            continue

        try:
            cvss_score = float(cvss_raw)
        except ValueError:
            continue

        findings.append(
            {
                "ip_address": host or "Unknown",
                "severity": risk,
                "cvss_score": cvss_score,
                "plugin_id": plugin_id,
                "title": name
            }
        )

    return findings
