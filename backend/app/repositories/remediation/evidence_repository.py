from sqlalchemy.orm import Session

from app.models.evidence_attachment import EvidenceAttachment


def _scope(query, org_id):
    """
    Restrict a query to one organization. `org_id=None` = no restriction.
    """

    if org_id is not None:
        query = query.filter(EvidenceAttachment.org_id == org_id)

    return query


def create_evidence_attachment(
    db: Session,
    **fields
):
    attachment = EvidenceAttachment(**fields)

    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    return attachment


def get_evidence_attachment(
    db: Session,
    attachment_id: int,
    org_id: int = None
):
    return (
        _scope(
            db.query(EvidenceAttachment)
            .filter(EvidenceAttachment.id == attachment_id),
            org_id
        )
        .first()
    )


def list_by_vulnerability(
    db: Session,
    vulnerability_id: int,
    org_id: int = None
):
    return (
        _scope(
            db.query(EvidenceAttachment)
            .filter(EvidenceAttachment.vulnerability_id == vulnerability_id),
            org_id
        )
        .all()
    )


def list_by_risk(
    db: Session,
    risk_id: int,
    org_id: int = None
):
    return (
        _scope(
            db.query(EvidenceAttachment)
            .filter(EvidenceAttachment.risk_id == risk_id),
            org_id
        )
        .all()
    )


def delete_evidence_attachment(
    db: Session,
    attachment: EvidenceAttachment
):
    db.delete(attachment)
    db.commit()
