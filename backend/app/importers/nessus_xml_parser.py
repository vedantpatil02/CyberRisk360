"""
CyberRisk360

Purpose:
Extract findings from native Nessus (.nessus) XML report exports.
"""

from defusedxml import ElementTree

# Nessus severity is an integer 0-4 (Info/Low/Medium/High/Critical).
# 0 (Info) is skipped, matching the CSV/PDF parsers' existing behavior
# of silently ignoring informational findings.
_SEVERITY_BY_LEVEL = {
    "1": "LOW",
    "2": "MEDIUM",
    "3": "HIGH",
    "4": "CRITICAL"
}


def extract_findings(
    content: str
):
    """
    Parse a native .nessus XML export
    (<NessusClientData_v2><Report><ReportHost name="...">
    <ReportItem pluginID="..." pluginName="..." severity="0-4">
    <cvss_base_score>...</cvss_base_score></ReportItem></ReportHost>
    </Report></NessusClientData_v2>) into the same finding dict shape
    the CSV and PDF parsers produce. Uses defusedxml to guard against
    XXE/entity-expansion attacks from untrusted uploads.
    """

    findings = []

    root = ElementTree.fromstring(content)

    for report_host in root.iter("ReportHost"):

        ip_address = report_host.get("name", "Unknown")

        for report_item in report_host.iter("ReportItem"):

            severity = _SEVERITY_BY_LEVEL.get(
                report_item.get("severity", "")
            )

            if not severity:
                continue

            plugin_id = report_item.get("pluginID", "").strip()
            title = report_item.get("pluginName", "").strip()

            cvss_element = (
                report_item.find("cvss3_base_score")
                if report_item.find("cvss3_base_score") is not None
                else report_item.find("cvss_base_score")
            )

            if not plugin_id or cvss_element is None or not cvss_element.text:
                continue

            try:
                cvss_score = float(cvss_element.text.strip())
            except ValueError:
                continue

            findings.append(
                {
                    "ip_address": ip_address,
                    "severity": severity,
                    "cvss_score": cvss_score,
                    "plugin_id": plugin_id,
                    "title": title
                }
            )

    return findings
