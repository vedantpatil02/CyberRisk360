"""
CyberRisk360

Purpose:
Executive dashboard
aggregating platform metrics.
"""

from app.models.asset import Asset
from app.models.vulnerability import (
    Vulnerability
)

from app.services.asset_risk_analysis import (
    get_asset_risk_summary
)

from app.services.control_risk_analysis import (
    get_control_risk_analysis
)

from app.models.control import Control


def get_executive_dashboard(
    db
):
    """
    Return executive summary
    across assets, vulnerabilities,
    compliance, and risk.
    """

    assets = (
        db.query(Asset)
        .all()
    )

    vulnerabilities = (
        db.query(Vulnerability)
        .all()
    )

    controls = (
        db.query(Control)
        .all()
    )

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
            db
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
            "nist-csf"
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