from sqlalchemy.orm import Session

from app.models.risk_treatment_history import RiskTreatmentHistory


def get_history_for_risk(
    db: Session,
    risk_id: int
):
    return (
        db.query(RiskTreatmentHistory)
        .filter(
            RiskTreatmentHistory.risk_id == risk_id
        )
        .order_by(RiskTreatmentHistory.created_at)
        .all()
    )


def record_history(
    db: Session,
    risk_id: int,
    action: str,
    new_status: str,
    org_id: int,
    previous_status: str = None,
    treatment_type: str = None,
    actor: str = None,
    note: str = None
):
    entry = RiskTreatmentHistory(
        risk_id=risk_id,
        action=action,
        previous_status=previous_status,
        new_status=new_status,
        treatment_type=treatment_type,
        org_id=org_id,
        actor=actor,
        note=note
    )

    db.add(entry)
    db.flush()

    return entry
