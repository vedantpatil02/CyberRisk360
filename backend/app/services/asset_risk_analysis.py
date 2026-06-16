"""
CyberRisk360

Purpose:
Calculate risk scores
for assets based on
associated vulnerabilities.
"""

from app.models.asset import Asset
from app.models.vulnerability import (
    Vulnerability
)


def get_asset_risk_summary(
    db
):
    """
    Return risk summary
    for all assets.
    """

    assets = (
        db.query(Asset)
        .all()
    )

    results = []

    for asset in assets:

        vulnerabilities = (
            db.query(Vulnerability)
            .filter(
                Vulnerability.asset_id
                == asset.id
            )
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

        risk_score = (
            critical * 10
            + high * 7
            + medium * 4
            + low * 1
        )

        results.append(
            {
                "asset":
                    asset.name
                    if asset.name
                    else asset.ip_address,

                "critical":
                    critical,

                "high":
                    high,

                "medium":
                    medium,

                "low":
                    low,

                "risk_score":
                    risk_score,

                "total_vulnerabilities":
                    len(vulnerabilities)
            }
        )

    results.sort(
        key=lambda asset:
            asset["risk_score"],
        reverse=True
    )

    return results