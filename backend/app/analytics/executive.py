"""
CyberRisk360

Purpose:
Executive dashboard
aggregating platform metrics.
"""

from app.repositories.assets.asset_repository import (
    get_all_assets
)
from app.repositories.vulnerabilities.vulnerability_repository import (
    get_all_vulnerabilities
)
from app.repositories.controls.control_repository import (
    get_all_controls
)

from app.analytics.asset_risk import (
    get_asset_risk_summary
)

from app.analytics.control_risk_analysis import (
    get_control_risk_analysis
)


def get_executive_dashboard(
    db,
    org_id=None
):
    """
    Return executive summary across assets, vulnerabilities, compliance,
    and risk, scoped to the organization (`org_id=None` = all orgs).
    """

    assets = get_all_assets(db, org_id=org_id)

    vulnerabilities = get_all_vulnerabilities(db, org_id=org_id)

    controls = get_all_controls(db)

    critical = 0
    high = 0
    medium = 0
    low = 0

    for vulnerability in vulnerabilities:

        severity = (
            vulnerability.severity
            .upper()
        )

        if severity == "CRITICAL":
            critical += 1

        elif severity == "HIGH":
            high += 1

        elif severity == "MEDIUM":
            medium += 1

        elif severity == "LOW":
            low += 1

    asset_risks = (
        get_asset_risk_summary(
            db,
            org_id=org_id
        )
    )

    top_asset = (
        asset_risks[0]
        if asset_risks
        else None
    )

    control_risks = (
        get_control_risk_analysis(
            db,
            "nist-csf",
            org_id=org_id
        )
    )

    top_control = (
        control_risks["controls"][0]
        if control_risks["controls"]
        else None
    )

    overall_control_risk = sum(
        control["risk_score"]
        for control
        in control_risks["controls"]
    )

    return {

        "assets": {
            "total":
                len(assets),

            "highest_risk_asset":
                top_asset
        },

        "vulnerabilities": {
            "total":
                len(vulnerabilities),

            "critical":
                critical,

            "high":
                high,

            "medium":
                medium,

            "low":
                low
        },

        "controls": {
            "total":
                len(controls)
        },

        "risk": {
            "overall_control_risk_score":
                overall_control_risk,

            "top_risky_control":
                top_control
        }
    }
