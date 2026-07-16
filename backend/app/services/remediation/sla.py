"""
CyberRisk360

Purpose:
Fixed-window SLA computation for vulnerability/risk remediation.
Shared by both domains since severity (Low/Medium/High/Critical) and
risk_level use identical values today.
"""

from datetime import datetime, timedelta, timezone

from app.core.constants import (
    VULNERABILITY_STATUS_CLOSED,
    VULNERABILITY_STATUS_VERIFIED,
    RISK_STATUS_MITIGATED,
    RISK_STATUS_ACCEPTED,
    RISK_STATUS_TRANSFERRED,
    RISK_STATUS_AVOIDED,
    RISK_STATUS_CLOSED,
)

# Hours allowed to remediate, by severity/risk_level. Unrecognized
# values fall back to the most lenient (Low) window rather than
# raising, so a due_date is always computable.
SLA_HOURS_BY_SEVERITY = {
    "Critical": 24,
    "High": 72,
    "Medium": 168,   # 7 days
    "Low": 720,      # 30 days
}

DEFAULT_SLA_HOURS = SLA_HOURS_BY_SEVERITY["Low"]

# Statuses past which a due_date is no longer considered breached,
# even if it's in the past.
VULNERABILITY_TERMINAL_STATUSES = (
    VULNERABILITY_STATUS_CLOSED,
    VULNERABILITY_STATUS_VERIFIED,
)
RISK_TERMINAL_STATUSES = (
    RISK_STATUS_MITIGATED,
    RISK_STATUS_ACCEPTED,
    RISK_STATUS_TRANSFERRED,
    RISK_STATUS_AVOIDED,
    RISK_STATUS_CLOSED,
)


def compute_due_date(level: str, from_dt: datetime = None) -> datetime:
    """
    Compute an SLA due_date from a severity/risk_level, anchored at
    from_dt (defaults to now, UTC).
    """

    hours = SLA_HOURS_BY_SEVERITY.get(level, DEFAULT_SLA_HOURS)
    anchor = from_dt or datetime.now(timezone.utc)

    return anchor + timedelta(hours=hours)


def is_sla_breached(
    due_date: datetime,
    status: str,
    terminal_statuses,
    now: datetime = None
) -> bool:
    """
    A due_date is breached only if it's in the past AND the record
    hasn't reached a terminal status. Never persisted - always
    computed at read/query time so it can't go stale.
    """

    if due_date is None or status in terminal_statuses:
        return False

    if due_date.tzinfo is None:
        # SQLite doesn't reliably round-trip tzinfo on
        # DateTime(timezone=True) columns - always written as UTC, so
        # it's safe to assume UTC when it comes back naive.
        due_date = due_date.replace(tzinfo=timezone.utc)

    reference = now or datetime.now(timezone.utc)

    return due_date < reference
