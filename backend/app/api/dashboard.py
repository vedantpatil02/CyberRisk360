from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.models.asset import Asset
from app.models.vulnerability import Vulnerability
from sqlalchemy import func
from app.services.grc_dashboard import get_grc_dashboard
from app.dependencies.rbac import require_role
from app.core.constants import ROLE_ADMIN, ROLE_ANALYST,ROLE_AUDITOR
from app.services.executive_dashboard import (
    get_executive_dashboard
)


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

@router.get(
    "/dashboard/grc/{framework_name}"
)
def grc_dashboard(
    framework_name: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
            ROLE_AUDITOR
        )
    )
):
    """
    Executive GRC dashboard.
    """

    return get_grc_dashboard(
        db,
        framework_name
    )

@router.get(
    "/dashboard/executive"
)
def executive_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
            ROLE_AUDITOR
        )
    )
):
    """
    Executive security dashboard.
    """

    return get_executive_dashboard(
        db
    )