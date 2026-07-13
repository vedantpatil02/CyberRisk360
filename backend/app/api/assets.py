from fastapi import Depends
from fastapi import APIRouter
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.schemas.asset import AssetCreate
from app.dependencies.database import get_db
from app.dependencies.security import (
    get_current_user
)
from app.dependencies.rbac import (
    require_role
)
from app.core.constants import *

from app.analytics.asset_risk import (
    get_asset_risk_summary
)

from app.repositories.assets.asset_repository import (
    get_all_assets,
    get_asset,
    create_asset as db_create_asset
)
from app.repositories.vulnerabilities.vulnerability_repository import (
    get_by_asset
)

router = APIRouter()

@router.post("/assets")
def create_asset(
    asset: AssetCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST
        )
    )
):

    db_create_asset(
        db,
        name=asset.name,
        asset_type=asset.asset_type,
        owner=asset.owner,
        criticality=asset.criticality,
        ip_address=asset.ip_address,
        environment=asset.environment
    )

    return {
        "message": "Asset created"
    }


@router.get("/assets")
def get_assets(
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):
    return get_all_assets(db)



@router.get(
    "/assets/{asset_id}/vulnerabilities"
)
def get_asset_vulnerabilities(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
            ROLE_AUDITOR
        )
    )
):

    vulnerabilities = get_by_asset(
        db,
        asset_id,
        order_by_cvss=True
    )

    results = []

    for vulnerability in vulnerabilities:

        results.append(
            {
                "id":
                    vulnerability.id,

                "plugin_id":
                    vulnerability.plugin_id,

                "title":
                    vulnerability.title,

                "severity":
                    vulnerability.severity,

                "cvss_score":
                    vulnerability.cvss_score,

                "status":
                    vulnerability.status
            }
        )

    return results


@router.get(
    "/assets/{asset_id}/summary"
)
def get_asset_summary(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
            ROLE_AUDITOR
        )
    )
):

    asset = get_asset(db, asset_id)

    if not asset:

        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    vulnerabilities = get_by_asset(db, asset_id)

    summary = {
        "asset_id": asset.id,
        "asset_name": asset.name,
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "total": len(vulnerabilities)
    }

    for vulnerability in vulnerabilities:

        severity = (
            vulnerability.severity
            .lower()
        )

        if severity in summary:
            summary[severity] += 1

    return summary

@router.get(
    "/assets/risk-summary"
)
def asset_risk_summary(
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
    Return risk scores
    for all assets.
    """

    return get_asset_risk_summary(
        db
    )
