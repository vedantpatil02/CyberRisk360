"""
CyberRisk360

Purpose:
Data access for the append-only audit trail.
"""

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def create_audit_log(
    db: Session,
    actor: str,
    action: str,
    entity_type: str = None,
    entity_id: str = None,
    ip_address: str = None,
    detail: str = None,
    org_id: int = None,
):
    """
    Insert one audit-log row. Does not commit - the caller controls the
    transaction boundary (see `services/audit/audit.py`). `org_id` may
    be None for org-less events (e.g. a failed login for an unknown
    email).
    """

    entry = AuditLog(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=(str(entity_id) if entity_id is not None else None),
        ip_address=ip_address,
        detail=detail,
        org_id=org_id,
    )

    db.add(entry)

    return entry


def get_audit_logs(
    db: Session,
    org_id: int = None,
    limit: int = 50,
    offset: int = 0,
    action: str = None,
    actor: str = None,
):
    """
    Return audit-log rows, most recent first, with optional filtering
    and pagination. Scoped to `org_id` (None = all orgs, for a
    super-admin).
    """

    query = db.query(AuditLog)

    if org_id is not None:
        query = query.filter(AuditLog.org_id == org_id)

    if action is not None:
        query = query.filter(AuditLog.action == action)

    if actor is not None:
        query = query.filter(AuditLog.actor == actor)

    return (
        query
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
