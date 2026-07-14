"""
CyberRisk360

Purpose:
Append-only audit trail of security-relevant actions (authentication,
account management, and state-changing domain operations). This is the
general audit log a GRC/compliance product is expected to keep - distinct
from `MappingHistory`, which records only vulnerability-to-control
mapping decisions.

Rows are never updated or deleted by the application.
"""

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import DateTime
from sqlalchemy.sql import func

from app.db.database import Base


class AuditLog(Base):

    __tablename__ = "audit_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Who performed the action - typically the authenticated user's
    # email. "anonymous" for pre-auth events (e.g. a failed login),
    # "system" for machine-initiated actions.
    actor = Column(
        String,
        nullable=False,
        index=True
    )

    # What happened, as a dotted event key: "login.success",
    # "login.failure", "user.register", "vulnerability.create", ...
    action = Column(
        String,
        nullable=False,
        index=True
    )

    # The kind of object acted on ("user", "vulnerability", ...) and its
    # id, stored as a string so one column works for every entity.
    entity_type = Column(
        String,
        nullable=True
    )

    entity_id = Column(
        String,
        nullable=True
    )

    # Source IP, when the action came through an HTTP request.
    ip_address = Column(
        String,
        nullable=True
    )

    # Free-form human-readable context (e.g. "role=analyst",
    # "reason=account locked"). Not machine-parsed.
    detail = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
