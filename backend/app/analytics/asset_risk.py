"""
CyberRisk360

Purpose:
Calculate risk scores
for assets based on
associated vulnerabilities.
"""

from app.repositories.assets.asset_repository import (
    get_all_assets
)
from app.repositories.vulnerabilities.vulnerability_repository import (
    get_by_asset
)


def get_asset_risk_summary(
    db,
    org_id=None
):
    """
    Return risk summary for all assets in the organization scope
    (`org_id=None` = all orgs, for a super-admin).
    """

    assets = get_all_assets(db, org_id=org_id)

    results = []

    for asset in assets:

        vulnerabilities = get_by_asset(db, asset.id, org_id=org_id)

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
