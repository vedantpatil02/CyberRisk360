from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.models.asset import Asset
from app.models.vulnerability import Vulnerability
from sqlalchemy import func

router = APIRouter()

@router.get(
    "/dashboard/overview"
)
def dashboard_overview(
    db: Session = Depends(get_db)
):

    assets = (
        db.query(Asset)
        .count()
    )

    vulnerabilities = (
        db.query(Vulnerability)
        .all()
    )

    summary = {
        "total_assets": assets,
        "total_vulnerabilities": len(vulnerabilities),
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "open": 0,
        "closed": 0
    }

    for vulnerability in vulnerabilities:

        severity = (
            vulnerability.severity
            .lower()
        )

        if severity in summary:
            summary[severity] += 1

        status = (
            vulnerability.status
            .lower()
        )

        if status in summary:
            summary[status] += 1

    top_assets = (
        db.query(
            Asset.id,
            Asset.name,
            func.count(
                Vulnerability.id
            ).label(
                "vulnerability_count"
            )
        )
        .join(
            Vulnerability,
            Vulnerability.asset_id
            == Asset.id
        )
        .group_by(
            Asset.id,
            Asset.name
        )
        .order_by(
            func.count(
                Vulnerability.id
            ).desc()
        )
        .limit(5)
        .all()
    )

    summary["top_assets"] = []

    for asset in top_assets:

        summary["top_assets"].append(
            {
                "asset_id": asset.id,
                "asset_name": asset.name,
                "vulnerability_count":
                    asset.vulnerability_count
            }
        )

    return summary