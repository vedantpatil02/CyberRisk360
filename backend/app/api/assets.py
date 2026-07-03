from fastapi import Depends
from fastapi import APIRouter
from sqlalchemy.orm import Session

from app.db.database import SessionLocal

from app.models.asset import Asset

from app.schemas.asset import AssetCreate
from app.dependencies.database import get_db
from app.core.constants import *

from app.models.vulnerability import Vulnerability

from app.analytics.asset_risk import (
    get_asset_risk_summary
)

router = APIRouter()

from app.dependencies.rbac import (
    require_role
)
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

    
    # Create a new asset record from request data

    new_asset = Asset(
        name=asset.name,
        asset_type=asset.asset_type,
        owner=asset.owner,
        criticality=asset.criticality,
        ip_address=asset.ip_address,
        environment=asset.environment
    )

    # Save asset into database
    db.add(new_asset)

    db.commit()

    return {
        "message": "Asset created"
    }


from app.dependencies.security import (
    get_current_user
)

@router.get("/assets")
def get_assets(
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):
    return db.query(Asset).all()



@router.get(
    "/assets/{asset_id}/vulnerabilities"
)
def get_asset_vulnerabilities(
    asset_id: int,
    db: Session = Depends(get_db)
):

    vulnerabilities = (
        db.query(
            Vulnerability
        )
        .filter(
            Vulnerability.asset_id
            == asset_id
        )
        .order_by(
            Vulnerability.cvss_score.desc()
        )
        .all()
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
    db: Session = Depends(get_db)
):

    asset = (
        db.query(Asset)
        .filter(
            Asset.id == asset_id
        )
        .first()
    )

    if not asset:

        return {
            "message": "Asset not found"
        }

    vulnerabilities = (
        db.query(
            Vulnerability
        )
        .filter(
            Vulnerability.asset_id
            == asset_id
        )
        .all()
    )

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