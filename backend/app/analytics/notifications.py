"""
CyberRisk360

Purpose:
In-app notification list. Computed live at read time, not stored or
pushed - no background-job mechanism exists in this codebase (no
Celery/APScheduler), same "always fresh, never stale" approach already
used for SLA breach (app/services/remediation/sla.py::is_sla_breached).

Currently covers evidence expiry only; a future sprint could add more
notification types (new criticals, SLA breach, import done - see
docs/ROADMAP.md Phase 5) by extending this function.
"""

from datetime import datetime, timedelta, timezone

from app.repositories.remediation.evidence_repository import list_with_expiry

# How far ahead "expiring soon" looks.
EXPIRING_SOON_WINDOW_DAYS = 30


def _as_aware_utc(value: datetime) -> datetime:
    # SQLite doesn't reliably round-trip tzinfo on DateTime(timezone=True)
    # columns - always written as UTC, so it's safe to assume UTC when
    # it comes back naive. Same handling as sla.py::is_sla_breached.
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def get_notifications(db, org_id=None):
    """
    Return evidence-expiry notifications for the caller's org
    (`org_id=None` = all orgs, for a super-admin), sorted soonest-first.
    """

    attachments = list_with_expiry(db, org_id=org_id)

    now = datetime.now(timezone.utc)
    soon_cutoff = now + timedelta(days=EXPIRING_SOON_WINDOW_DAYS)

    notifications = []

    for attachment in attachments:
        expires_at = _as_aware_utc(attachment.expires_at)

        if expires_at < now:
            notification_type = "evidence_expired"
            message = f'Evidence "{attachment.file_name}" has expired'
        elif expires_at <= soon_cutoff:
            notification_type = "evidence_expiring_soon"
            message = f'Evidence "{attachment.file_name}" expires soon'
        else:
            continue

        entity_type = "vulnerability" if attachment.vulnerability_id else "risk"
        entity_id = attachment.vulnerability_id or attachment.risk_id

        notifications.append({
            "type": notification_type,
            "message": message,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "expires_at": attachment.expires_at,
        })

    notifications.sort(key=lambda notification: notification["expires_at"])

    return notifications
