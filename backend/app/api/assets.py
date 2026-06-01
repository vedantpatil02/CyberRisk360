from fastapi import Depends
from fastapi import APIRouter
from sqlalchemy.orm import Session

from app.database import SessionLocal

from app.models.asset import Asset

from app.schemas.asset import AssetCreate
from app.dependencies import get_db



router = APIRouter()


@router.post("/assets")
def create_asset(asset: AssetCreate, db: Session = Depends(get_db)):

    

    new_asset = Asset(
        name=asset.name,
        asset_type=asset.asset_type,
        owner=asset.owner,
        criticality=asset.criticality,
        ip_address=asset.ip_address,
        environment=asset.environment
    )

    db.add(new_asset)

    db.commit()

    return {
        "message": "Asset created"
    }


@router.get("/assets")
def get_assets(
    db: Session = Depends(get_db)
):
    return db.query(Asset).all()