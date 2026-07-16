"""
CyberRisk360

Purpose:
Stores metadata for evidence files uploaded against a vulnerability or
a risk (e.g. a remediation screenshot, a rescan report). The file
itself lives on disk under UPLOAD_DIR/evidence/; this table tracks
who uploaded what, when, and which record it evidences.
"""

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class EvidenceAttachment(Base):
    """
    Evidence attachment table.

    Exactly one of vulnerability_id / risk_id is set per row - the
    two nullable FKs (rather than a polymorphic entity_type/entity_id
    pair) keep real referential integrity, matching how
    Vulnerability.asset_id/risk_id already do this in this codebase.
    The "exactly one" invariant is enforced in the service layer.
    """

    __tablename__ = "evidence_attachments"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    vulnerability_id = Column(
        Integer,
        ForeignKey("vulnerabilities.id"),
        nullable=True,
        index=True
    )

    risk_id = Column(
        Integer,
        ForeignKey("risks.id"),
        nullable=True,
        index=True
    )

    # Original uploaded filename.
    file_name = Column(
        String,
        nullable=False
    )

    # Path on disk under UPLOAD_DIR/evidence/.
    stored_path = Column(
        String,
        nullable=False
    )

    content_type = Column(
        String,
        nullable=True
    )

    file_size = Column(
        Integer,
        nullable=True
    )

    uploaded_by_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    org_id = Column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
        index=True
    )

    uploaded_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Optional - no expiry by default. Drives the in-app notification
    # list (app/analytics/notifications.py), computed live at read
    # time rather than via a background job (none exists in this
    # codebase - same "never persisted, always fresh" approach as
    # is_sla_breached in app/services/remediation/sla.py).
    expires_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    vulnerability = relationship("Vulnerability", back_populates="evidence")
    risk = relationship("Risk", back_populates="evidence")
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_id])
