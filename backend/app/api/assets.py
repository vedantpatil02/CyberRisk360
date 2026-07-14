from typing import Optional

from fastapi import Depends
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Query
from sqlalchemy.orm import Session

from app.schemas.asset import AssetCreate
from app.dependencies.database import get_db
from app.dependencies.security import (
    get_current_user
)
from app.dependencies.rbac import (
    require_role
)
from app.dependencies.tenancy import org_scope, org_home
from app.core.constants import *

from app.analytics.asset_risk import (
    get_asset_risk_summary
)

from app.repositories.assets.asset_repository import (
    get_all_assets,
    query_assets,
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
    org_id=Depends(org_home),
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
        environment=asset.environment,
        org_id=org_id
    )

    return {
        "message": "Asset created"
    }


@router.get("/assets")
def get_assets(
    limit: Optional[int] = Query(None, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    criticality: Optional[str] = None,
    environment: Optional[str] = None,
    asset_type: Optional[str] = None,
    sort_by: str = Query("id"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    current_user=Depends(
        get_current_user
    ),
    org_id=Depends(org_scope),
    db: Session = Depends(get_db)
):
    """
    List assets (scoped to the caller's organization). Optional
    `criticality`/`environment`/`asset_type` filters, `sort_by` +
    `order`, and `limit`/`offset` pagination.
    """

    return query_assets(
        db,
        org_id=org_id,
        limit=limit,
        offset=offset,
        criticality=criticality,
        environment=environment,
        asset_type=asset_type,
        sort_by=sort_by,
        order=order,
    )



@router.get(
    "/assets/{asset_id}/vulnerabilities"
)
def get_asset_vulnerabilities(
    asset_id: int,
    db: Session = Depends(get_db),
    org_id=Depends(org_scope),
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
        order_by_cvss=True,
        org_id=org_id
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
    org_id=Depends(org_scope),
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
            ROLE_AUDITOR
        )
    )
):

    asset = get_asset(db, asset_id, org_id=org_id)

    if not asset:

        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    vulnerabilities = get_by_asset(db, asset_id, org_id=org_id)

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
    org_id=Depends(org_scope),
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
        db,
        org_id=org_id
    )
