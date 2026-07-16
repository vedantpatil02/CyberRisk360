"""
CyberRisk360

Purpose:
Write entries to the audit trail. Endpoints/services call `record_audit`
at security-relevant points; this module owns the (small) transaction
policy and the canonical action keys.
"""

from app.repositories.audit.audit_repository import create_audit_log
from app.core.net import get_client_ip


# Canonical action keys - referenced from call sites so a typo shows up
# as an import error, not a silently-mismatched string.
ACTION_LOGIN_SUCCESS = "login.success"
ACTION_LOGIN_FAILURE = "login.failure"
ACTION_LOGIN_LOCKED = "login.locked"
ACTION_USER_REGISTER = "user.register"
ACTION_USER_PASSWORD_CHANGE = "user.password_change"
ACTION_USER_PASSWORD_RESET = "user.password_reset"
ACTION_USER_ACTIVATE = "user.activate"
ACTION_USER_DEACTIVATE = "user.deactivate"
ACTION_USER_ROLE_CHANGE = "user.role_change"
ACTION_IMPORT_UPLOAD = "import.upload"
ACTION_MAPPING_APPROVE = "mapping.approve"
ACTION_MAPPING_REJECT = "mapping.reject"
ACTION_RISK_GENERATE = "risk.generate"
ACTION_VULNERABILITY_ASSIGN = "vulnerability.assign"
ACTION_RISK_ASSIGN = "risk.assign"
ACTION_RISK_TREATMENT_PROPOSE = "risk.treatment_propose"
ACTION_RISK_TREATMENT_APPROVE = "risk.treatment_approve"
ACTION_RISK_TREATMENT_REJECT = "risk.treatment_reject"

# Audit *engagement* lifecycle events (the Audit/AuditFinding models) -
# not to be confused with this module's own generic activity trail,
# which these constants themselves feed into via record_audit().
ACTION_AUDIT_CREATE = "audit.create"
ACTION_AUDIT_CLOSE = "audit.close"
ACTION_AUDIT_FINDING_CREATE = "audit.finding_create"

ANONYMOUS_ACTOR = "anonymous"
SYSTEM_ACTOR = "system"


def client_ip(request):
    """
    Best-effort source IP for an incoming request. Honors
    `X-Forwarded-For` only when `TRUST_PROXY_HEADERS` is enabled (see
    `app/core/net.py`).
    """

    return get_client_ip(request)


def record_audit(
    db,
    action: str,
    actor: str = ANONYMOUS_ACTOR,
    entity_type: str = None,
    entity_id=None,
    ip_address: str = None,
    detail: str = None,
    org_id: int = None,
    commit: bool = True,
):
    """
    Append one entry to the audit trail.

    `org_id` scopes the event to an organization; leave it None for
    org-less events (unknown-email login failure, platform actions).

    `commit=True` (default) persists immediately - use for standalone
    events such as login attempts. `commit=False` lets the entry ride
    along with a caller that will commit its own work, so the audit row
    and the change it describes land in the same transaction.
    """

    entry = create_audit_log(
        db,
        actor=actor or ANONYMOUS_ACTOR,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
        detail=detail,
        org_id=org_id,
    )

    if commit:
        db.commit()

    return entry
