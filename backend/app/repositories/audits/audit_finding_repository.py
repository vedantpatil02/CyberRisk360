from sqlalchemy.orm import Session

from app.models.audit_finding import AuditFinding


def list_findings_for_audit(
    db: Session,
    audit_id: int
):
    return (
        db.query(AuditFinding)
        .filter(AuditFinding.audit_id == audit_id)
        .order_by(AuditFinding.created_at)
        .all()
    )


def get_finding(
    db: Session,
    finding_id: int
):
    return (
        db.query(AuditFinding)
        .filter(AuditFinding.id == finding_id)
        .first()
    )


def create_finding(
    db: Session,
    **fields
):
    finding = AuditFinding(**fields)

    db.add(finding)
    db.commit()
    db.refresh(finding)

    return finding


def update_finding(
    db: Session,
    finding: AuditFinding,
    updates: dict
):
    for field, value in updates.items():
        setattr(finding, field, value)

    db.commit()
    db.refresh(finding)

    return finding
