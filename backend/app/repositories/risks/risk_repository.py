from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.risk import Risk
from app.services.remediation.sla import RISK_TERMINAL_STATUSES


RISK_SORT_COLUMNS = {
    "id": Risk.id,
    "risk_score": Risk.risk_score,
    "risk_level": Risk.risk_level,
    "status": Risk.status,
    "due_date": Risk.due_date,
    "assignee_id": Risk.assignee_id,
}


def _scope(query, org_id):
    """
    Restrict a query to one organization. `org_id=None` = no restriction.
    """

    if org_id is not None:
        query = query.filter(Risk.org_id == org_id)

    return query


def get_all_risks(
    db: Session,
    org_id: int = None
):
    return (
        _scope(db.query(Risk), org_id)
        .all()
    )


def query_risks(
    db: Session,
    org_id: int = None,
    limit: int = None,
    offset: int = 0,
    risk_level: str = None,
    status: str = None,
    source: str = None,
    asset_id: int = None,
    assignee_id: int = None,
    sla_breached: bool = None,
    sort_by: str = "id",
    order: str = "asc",
):
    """
    List risks with optional filtering, sorting, and pagination, scoped
    to `org_id` (None = all orgs).
    """

    query = _scope(db.query(Risk), org_id)

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

    if assignee_id is not None:
        query = query.filter(Risk.assignee_id == assignee_id)

    if sla_breached is not None:
        # Breached: has a due_date in the past and hasn't reached a
        # terminal status. Computed at query time (never stored) - see
        # services/remediation/sla.py.
        breach_condition = (
            Risk.due_date.isnot(None)
            & (Risk.due_date < datetime.now(timezone.utc))
            & Risk.status.notin_(RISK_TERMINAL_STATUSES)
        )
        query = query.filter(
            breach_condition if sla_breached else ~breach_condition
        )

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
    risk_id: int,
    org_id: int = None
):
    return (
        _scope(
            db.query(Risk).filter(Risk.id == risk_id),
            org_id
        )
        .first()
    )


def get_auto_risk_by_asset(
    db: Session,
    asset_id: int,
    org_id: int = None
):
    """
    Return the engine-generated ("auto") risk for an asset, if any.
    There is at most one per asset; manual risks are never returned.
    """

    return (
        _scope(
            db.query(Risk).filter(
                Risk.asset_id == asset_id,
                Risk.source == "auto"
            ),
            org_id
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
