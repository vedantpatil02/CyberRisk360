from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.vulnerability import Vulnerability


ASSET_SORT_COLUMNS = {
    "id": Asset.id,
    "name": Asset.name,
    "criticality": Asset.criticality,
    "environment": Asset.environment,
}


def get_all_assets(
    db: Session
):
    return (
        db.query(Asset)
        .all()
    )


def query_assets(
    db: Session,
    limit: int = None,
    offset: int = 0,
    criticality: str = None,
    environment: str = None,
    asset_type: str = None,
    sort_by: str = "id",
    order: str = "asc",
):
    """
    List assets with optional filtering, sorting, and pagination. With
    no arguments this returns every row.
    """

    query = db.query(Asset)

    if criticality is not None:
        query = query.filter(
            func.lower(Asset.criticality) == criticality.lower()
        )

    if environment is not None:
        query = query.filter(
            func.lower(Asset.environment) == environment.lower()
        )

    if asset_type is not None:
        query = query.filter(
            func.lower(Asset.asset_type) == asset_type.lower()
        )

    column = ASSET_SORT_COLUMNS.get(sort_by, Asset.id)
    query = query.order_by(
        column.desc() if order == "desc" else column.asc()
    )

    if offset:
        query = query.offset(offset)

    if limit is not None:
        query = query.limit(limit)

    return query.all()


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
