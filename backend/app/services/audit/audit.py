"""
CyberRisk360

Purpose:
Write entries to the audit trail. Endpoints/services call `record_audit`
at security-relevant points; this module owns the (small) transaction
policy and the canonical action keys.
"""

from app.repositories.audit.audit_repository import create_audit_log


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
ACTION_IMPORT_UPLOAD = "import.upload"
ACTION_MAPPING_APPROVE = "mapping.approve"
ACTION_MAPPING_REJECT = "mapping.reject"
ACTION_RISK_GENERATE = "risk.generate"

ANONYMOUS_ACTOR = "anonymous"
SYSTEM_ACTOR = "system"


def client_ip(request):
    """
    Best-effort source IP for an incoming request.

    Trusts `request.client.host` directly - correct with no reverse
    proxy in front (the current deployment). If a proxy is ever added,
    this is the single place to start honoring `X-Forwarded-For` (see
    the matching note on rate limiting in TODO.md).
    """

    if request is None or request.client is None:
        return None

    return request.client.host


def record_audit(
    db,
    action: str,
    actor: str = ANONYMOUS_ACTOR,
    entity_type: str = None,
    entity_id=None,
    ip_address: str = None,
    detail: str = None,
    commit: bool = True,
):
    """
    Append one entry to the audit trail.

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
    )

    if commit:
        db.commit()

    return entry
