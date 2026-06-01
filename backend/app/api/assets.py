from fastapi import Depends
from fastapi import APIRouter
from sqlalchemy.orm import Session

from app.database import SessionLocal

from app.models.asset import Asset

from app.schemas.asset import AssetCreate
from app.dependencies.database import get_db



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
            "admin",
            "analyst"
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

