from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.analytics.grc import get_grc_dashboard
from app.dependencies.rbac import require_role
from app.dependencies.tenancy import org_scope
from app.core.constants import READ_ROLES
from app.analytics.executive import (
    get_executive_dashboard
)

from app.repositories.assets.asset_repository import (
    count_assets,
    get_top_assets_by_vulnerability_count
)
from app.repositories.vulnerabilities.vulnerability_repository import (
    get_all_vulnerabilities
)


router = APIRouter()

@router.get(
    "/dashboard/overview"
)
def dashboard_overview(
    db: Session = Depends(get_db),
    org_id=Depends(org_scope)
):

    assets = count_assets(db, org_id=org_id)

    vulnerabilities = get_all_vulnerabilities(db, org_id=org_id)

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

    top_assets = get_top_assets_by_vulnerability_count(
        db, org_id=org_id, limit=5
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
    org_id=Depends(org_scope),
    current_user=Depends(
        require_role(*READ_ROLES)
    )
):
    """
    Executive GRC dashboard.
    """

    return get_grc_dashboard(
        db,
        framework_name,
        org_id=org_id
    )

@router.get(
    "/dashboard/executive"
)
def executive_dashboard(
    db: Session = Depends(get_db),
    org_id=Depends(org_scope),
    current_user=Depends(
        require_role(*READ_ROLES)
    )
):
    """
    Executive security dashboard.
    """

    return get_executive_dashboard(
        db,
        org_id=org_id
    )
