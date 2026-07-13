from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.vulnerability import Vulnerability


def get_all_assets(
    db: Session
):
    return (
        db.query(Asset)
        .all()
    )


def count_assets(
    db: Session
):
    return (
        db.query(Asset)
        .count()
    )


def get_top_assets_by_vulnerability_count(
    db: Session,
    limit: int = 5
):
    return (
        db.query(
            Asset.id,
            Asset.name,
            func.count(Vulnerability.id).label(
                "vulnerability_count"
            )
        )
        .join(
            Vulnerability,
            Vulnerability.asset_id == Asset.id
        )
        .group_by(
            Asset.id,
            Asset.name
        )
        .order_by(
            func.count(Vulnerability.id).desc()
        )
        .limit(limit)
        .all()
    )


def get_asset(
    db: Session,
    asset_id: int
):
    return (
        db.query(Asset)
        .filter(
            Asset.id == asset_id
        )
        .first()
    )


def get_asset_by_ip(
    db: Session,
    ip_address: str
):
    return (
        db.query(Asset)
        .filter(
            Asset.ip_address == ip_address
        )
        .first()
    )


def create_asset(
    db: Session,
    name: str,
    asset_type: str,
    owner: str,
    criticality: str,
    ip_address: str = None,
    environment: str = None
):
    asset = Asset(
        name=name,
        asset_type=asset_type,
        owner=owner,
        criticality=criticality,
        ip_address=ip_address,
        environment=environment
    )

    db.add(asset)
    db.commit()
    db.refresh(asset)

    return asset
