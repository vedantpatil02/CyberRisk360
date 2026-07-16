"""
CyberRisk360

Purpose:
Audit engagement model - a scheduled/ongoing compliance audit against
(optionally) one framework, with a lifecycle status and findings.

Distinct from AuditLog (app/models/audit_log.py), which is the
generic security/activity trail (login, CRUD events) - this is the
GRC "audit engagement" concept: scope, schedule, findings.
"""

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Audit(Base):

    __tablename__ = "audits"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    title = Column(
        String,
        nullable=False
    )

    # An audit may or may not be scoped to one compliance framework.
    framework_id = Column(
        Integer,
        ForeignKey("frameworks.id"),
        nullable=True
    )

    # Real user reference, same convention as Risk.assignee_id /
    # Vulnerability.assignee_id - validated same-org at the API layer.
    lead_auditor_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )

    scope = Column(
        String,
        nullable=True
    )

    # Planned / In Progress / Completed / Closed
    status = Column(
        String,
        nullable=False,
        default="Planned"
    )

    start_date = Column(
        DateTime(timezone=True),
        nullable=True
    )

    end_date = Column(
        DateTime(timezone=True),
        nullable=True
    )

    org_id = Column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
        index=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    framework = relationship("Framework")

    lead_auditor = relationship("User", foreign_keys=[lead_auditor_id])

    findings = relationship(
        "AuditFinding",
        back_populates="audit",
        cascade="all, delete-orphan"
    )
