"""
CyberRisk360

Purpose:
Business logic for the Risk Treatment + Approval workflow: propose a
treatment (mitigate/accept/transfer/avoid) and approve or reject it.
Mirrors app/services/mapping/mapping_service.py's review_mapping shape.
"""

from datetime import datetime, timezone

from app.core.constants import (
    RISK_STATUS_OPEN,
    RISK_STATUS_UNDER_REVIEW,
    RISK_STATUS_CLOSED,
    RISK_TREATMENT_STATUS_BY_TYPE,
    RISK_APPROVAL_PENDING,
    RISK_APPROVAL_APPROVED,
    RISK_APPROVAL_REJECTED,
)

from app.repositories.risks.risk_repository import (
    get_risk,
    set_treatment_state
)

from app.repositories.risks.risk_treatment_history_repository import (
    get_history_for_risk,
    record_history
)


def get_treatment_history(db, risk_id):
    return get_history_for_risk(db, risk_id)


def propose_treatment(
    db,
    risk_id: int,
    treatment_type: str,
    justification: str,
    actor: str = None,
    org_id=None
):
    """
    Propose a treatment for a risk, scoped to `org_id` (None = any org,
    for a super-admin). Returns None if the risk doesn't exist (or
    belongs to another org) so the API layer turns that into a 404.
    Raises ValueError if the risk is already closed - a closed risk has
    nothing left to treat.
    """

    risk = get_risk(db, risk_id, org_id=org_id)

    if not risk:
        return None

    if risk.status == RISK_STATUS_CLOSED:
        raise ValueError("Cannot propose a treatment for a closed risk")

    previous_status = risk.status
    new_status = RISK_STATUS_UNDER_REVIEW

    set_treatment_state(
        db,
        risk,
        status=new_status,
        approval_status=RISK_APPROVAL_PENDING,
        treatment_type=treatment_type,
        treatment_justification=justification,
        approved_by=None,
        approved_at=None
    )

    record_history(
        db,
        risk_id=risk.id,
        action="proposed",
        previous_status=previous_status,
        new_status=new_status,
        treatment_type=treatment_type,
        org_id=risk.org_id,
        actor=actor,
        note=justification
    )

    db.commit()
    db.refresh(risk)

    return risk


def review_treatment(
    db,
    risk_id: int,
    approve: bool,
    reviewer: str = None,
    note: str = None,
    org_id=None
):
    """
    Approve or reject a risk's pending treatment, scoped to `org_id`
    (None = any org, for a super-admin). Returns None if the risk
    doesn't exist (or belongs to another org). Raises ValueError if
    there's no pending treatment to review.
    """

    risk = get_risk(db, risk_id, org_id=org_id)

    if not risk:
        return None

    if risk.approval_status != RISK_APPROVAL_PENDING:
        raise ValueError("Risk has no pending treatment to review")

    previous_status = risk.status

    if approve:
        new_status = RISK_TREATMENT_STATUS_BY_TYPE[risk.treatment_type]
        approval_status = RISK_APPROVAL_APPROVED
    else:
        # Rejected - back to Open for reconsideration, not left "Under
        # Review" forever.
        new_status = RISK_STATUS_OPEN
        approval_status = RISK_APPROVAL_REJECTED

    set_treatment_state(
        db,
        risk,
        status=new_status,
        approval_status=approval_status,
        approved_by=reviewer,
        approved_at=datetime.now(timezone.utc)
    )

    record_history(
        db,
        risk_id=risk.id,
        action="approved" if approve else "rejected",
        previous_status=previous_status,
        new_status=new_status,
        treatment_type=risk.treatment_type,
        org_id=risk.org_id,
        actor=reviewer,
        note=note
    )

    db.commit()
    db.refresh(risk)

    return risk
