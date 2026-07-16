from sqlalchemy.orm import Session

from app.models.audit import Audit


AUDIT_SORT_COLUMNS = {
    "id": Audit.id,
    "title": Audit.title,
    "status": Audit.status,
    "start_date": Audit.start_date,
    "end_date": Audit.end_date,
}


def _scope(query, org_id):
    """
    Restrict a query to one organization. `org_id=None` = no restriction
    (a platform super-admin reading across all orgs).
    """

    if org_id is not None:
        query = query.filter(Audit.org_id == org_id)

    return query


def query_audits(
    db: Session,
    org_id: int = None,
    limit: int = None,
    offset: int = 0,
    status: str = None,
    framework_id: int = None,
    sort_by: str = "id",
    order: str = "asc",
):
    """
    List audits with optional filtering, sorting, and pagination, scoped
    to `org_id` (None = all orgs).
    """

    query = _scope(db.query(Audit), org_id)

    if status is not None:
        query = query.filter(Audit.status == status)

    if framework_id is not None:
        query = query.filter(Audit.framework_id == framework_id)

    column = AUDIT_SORT_COLUMNS.get(sort_by, Audit.id)
    query = query.order_by(
        column.desc() if order == "desc" else column.asc()
    )

    if offset:
        query = query.offset(offset)

    if limit is not None:
        query = query.limit(limit)

    return query.all()


def get_audit(
    db: Session,
    audit_id: int,
    org_id: int = None
):
    return (
        _scope(
            db.query(Audit).filter(Audit.id == audit_id),
            org_id
        )
        .first()
    )


def create_audit(
    db: Session,
    **fields
):
    audit = Audit(**fields)

    db.add(audit)
    db.commit()
    db.refresh(audit)

    return audit


def update_audit(
    db: Session,
    audit: Audit,
    updates: dict
):
    for field, value in updates.items():
        setattr(audit, field, value)

    db.commit()
    db.refresh(audit)

    return audit
