from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.risk import Risk


RISK_SORT_COLUMNS = {
    "id": Risk.id,
    "risk_score": Risk.risk_score,
    "risk_level": Risk.risk_level,
    "status": Risk.status,
}


def get_all_risks(
    db: Session
):
    return (
        db.query(Risk)
        .all()
    )


def query_risks(
    db: Session,
    limit: int = None,
    offset: int = 0,
    risk_level: str = None,
    status: str = None,
    source: str = None,
    asset_id: int = None,
    sort_by: str = "id",
    order: str = "asc",
):
    """
    List risks with optional filtering, sorting, and pagination. With no
    arguments this returns every row.
    """

    query = db.query(Risk)

    if risk_level is not None:
        query = query.filter(
            func.lower(Risk.risk_level) == risk_level.lower()
        )

    if status is not None:
        query = query.filter(
            func.lower(Risk.status) == status.lower()
        )

    if source is not None:
        query = query.filter(Risk.source == source)

    if asset_id is not None:
        query = query.filter(Risk.asset_id == asset_id)

    column = RISK_SORT_COLUMNS.get(sort_by, Risk.id)
    query = query.order_by(
        column.desc() if order == "desc" else column.asc()
    )

    if offset:
        query = query.offset(offset)

    if limit is not None:
        query = query.limit(limit)

    return query.all()


def get_risk(
    db: Session,
    risk_id: int
):
    return (
        db.query(Risk)
        .filter(
            Risk.id == risk_id
        )
        .first()
    )


def get_auto_risk_by_asset(
    db: Session,
    asset_id: int
):
    """
    Return the engine-generated ("auto") risk for an asset, if any.
    There is at most one per asset; manual risks are never returned.
    """

    return (
        db.query(Risk)
        .filter(
            Risk.asset_id == asset_id,
            Risk.source == "auto"
        )
        .first()
    )


def create_risk(
    db: Session,
    **fields
):
    risk = Risk(**fields)

    db.add(risk)
    db.commit()
    db.refresh(risk)

    return risk


def update_risk(
    db: Session,
    risk: Risk,
    updates: dict
):
    for field, value in updates.items():
        setattr(risk, field, value)

    db.commit()

    return risk
