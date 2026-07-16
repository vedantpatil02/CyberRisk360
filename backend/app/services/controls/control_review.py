"""
CyberRisk360

Purpose:
Submit a control implementation-status review: snapshot the previous
status, apply the new one, and record the review event. Plain CRUD
(listing review history) is simple enough to call the repository
directly from the API layer - this module exists only for the
multi-step submit logic, same justification as
app/services/audits/audit_workflow.py and
app/services/risks/risk_treatment.py.
"""

from app.repositories.controls.control_repository import (
    get_control,
    update_control_status
)
from app.repositories.controls.control_review_repository import (
    create_review
)


def submit_review(
    db,
    control_id: int,
    new_status: str,
    notes: str = None,
    reviewer: str = None,
    org_id=None
):
    """
    Review a control's implementation status, recording the change.
    Returns None if the control doesn't exist. `org_id` scopes the
    review *event* to an organization - Control itself is shared
    reference data, not org-scoped.
    """

    control = get_control(db, control_id)

    if not control:
        return None

    previous_status = control.status

    update_control_status(db, control, new_status)

    return create_review(
        db,
        control_id=control_id,
        reviewer=reviewer,
        previous_status=previous_status,
        new_status=new_status,
        notes=notes,
        org_id=org_id
    )
