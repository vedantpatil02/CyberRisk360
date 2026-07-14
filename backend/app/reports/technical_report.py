"""
CyberRisk360

Purpose:
Technical Vulnerability report - the full finding register for security
analysts, grouped by severity with remediation guidance.
"""

from app.repositories.assets.asset_repository import (
    get_all_assets
)
from app.repositories.vulnerabilities.vulnerability_repository import (
    get_all_vulnerabilities
)

from app.reports.common import (
    build_envelope,
    severity_breakdown,
    status_breakdown
)


# Fixed presentation order so the most urgent findings lead the report.
# Anything with an unrecognized severity falls into "unknown" last.
SEVERITY_ORDER = ["critical", "high", "medium", "low", "unknown"]


def _finding_row(vulnerability, asset_names):
    """
    Flatten a vulnerability ORM row into a template-friendly dict.
    """

    return {
        "id": vulnerability.id,
        "title": vulnerability.title,
        "severity": vulnerability.severity,
        "cvss_score": vulnerability.cvss_score,
        "cve_id": vulnerability.cve_id,
        "plugin_id": vulnerability.plugin_id,
        "ip_address": vulnerability.ip_address,
        "asset":
            asset_names.get(vulnerability.asset_id),
        "status": vulnerability.status,
        "owner": vulnerability.owner,
        "description": vulnerability.description,
        "solution": vulnerability.solution,
    }


def build_technical_report(db, generated_by=None, org_id=None):
    """
    Build the structured Technical Vulnerability report, scoped to
    `org_id` (None = all orgs).
    """

    assets = get_all_assets(db, org_id=org_id)
    asset_names = {
        asset.id: (asset.name or asset.ip_address)
        for asset in assets
    }

    vulnerabilities = get_all_vulnerabilities(db, org_id=org_id)

    # Group findings by severity bucket, ordered most-severe first.
    grouped = {severity: [] for severity in SEVERITY_ORDER}

    for vulnerability in vulnerabilities:

        bucket = (vulnerability.severity or "").lower()

        if bucket not in grouped:
            bucket = "unknown"

        grouped[bucket].append(
            _finding_row(vulnerability, asset_names)
        )

    # Within a severity bucket, worst CVSS first.
    for bucket in grouped.values():
        bucket.sort(
            key=lambda row: row["cvss_score"] or 0,
            reverse=True
        )

    findings_by_severity = [
        {"severity": severity, "findings": grouped[severity]}
        for severity in SEVERITY_ORDER
        if grouped[severity]
    ]

    report = build_envelope(
        report_type="Technical Vulnerability Report",
        title="Technical Vulnerability Report",
        generated_by=generated_by
    )

    report["sections"] = {
        "summary": {
            "total_findings": len(vulnerabilities),
            "by_severity": severity_breakdown(vulnerabilities),
            "by_status": status_breakdown(vulnerabilities),
            "affected_assets": len(
                {
                    vulnerability.asset_id
                    for vulnerability in vulnerabilities
                    if vulnerability.asset_id is not None
                }
            ),
        },
        "findings_by_severity": findings_by_severity,
    }

    return report
