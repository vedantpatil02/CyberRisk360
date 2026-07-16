"""
CyberRisk360

Purpose:
Lifecycle logic for audit engagements: closing an audit, and updating
an audit finding's status. Plain CRUD (create/list/get/update) is
simple enough to call the repository directly from the API layer
(same convention as app/api/risks.py) - this module exists only for
the state-transition logic, same justification as
app/services/risks/risk_treatment.py.
"""

from app.core.constants import AUDIT_STATUS_CLOSED

from app.repositories.audits.audit_repository import (
    get_audit,
    update_audit
)
from app.repositories.audits.audit_finding_repository import (
    get_finding,
    update_finding
)


def close_audit(db, audit_id: int, org_id=None):
    """
    Close an audit engagement, scoped to `org_id` (None = any org, for
    a super-admin). Returns None if the audit doesn't exist (or
    belongs to another org). Raises ValueError if already closed.
    """

    audit = get_audit(db, audit_id, org_id=org_id)

    if not audit:
        return None

    if audit.status == AUDIT_STATUS_CLOSED:
        raise ValueError("Audit is already closed")

    return update_audit(db, audit, {"status": AUDIT_STATUS_CLOSED})


def update_finding_status(db, finding_id: int, status: str, org_id=None):
    """
    Update an audit finding's status, scoped to `org_id` via its
    parent audit (None = any org, for a super-admin). Returns None if
    the finding doesn't exist (or its audit belongs to another org).
    """

    finding = get_finding(db, finding_id)

    if not finding:
        return None

    if org_id is not None and finding.audit.org_id != org_id:
        return None

    return update_finding(db, finding, {"status": status})
