"""
CyberRisk360

Purpose:
Stores organizational risks and their
associated business impact.
"""

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class Risk(Base):
    """
    Risk register table.

    Each record represents a business,
    operational, or cybersecurity risk.
    """

    __tablename__ = "risks"

    # Unique Risk Identifier
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Short risk title
    title = Column(
        String,
        nullable=False
    )

    # Detailed risk description
    description = Column(
        String,
        nullable=False
    )

    # Asset affected by the risk
    asset_id = Column(
        Integer,
        ForeignKey("assets.id")
    )

    # Business impact score (1-5)
    impact = Column(
        Integer,
        nullable=False
    )

    # Probability score (1-5)
    likelihood = Column(
        Integer,
        nullable=False
    )

    # Calculated score
    risk_score = Column(
        Integer
    )

    # Low / Medium / High / Critical
    risk_level = Column(
        String
    )

    # Person responsible for treatment
    owner = Column(
        String
    )

    # Open / Under Review / Mitigated / Accepted / Transferred / Avoided
    # / Closed
    status = Column(
        String,
        default="Open"
    )

    # Risk Treatment Workflow: mitigate / accept / transfer / avoid -
    # what was proposed. Approval drives `status` to the matching
    # terminal value (see app/services/risks/risk_treatment.py).
    treatment_type = Column(
        String,
        nullable=True
    )

    treatment_justification = Column(
        String,
        nullable=True
    )

    # pending / approved / rejected
    approval_status = Column(
        String,
        nullable=True
    )

    # Reviewer identity - a string (email), not a User FK, matching the
    # existing reviewed_by convention on VulnerabilityControlMapping.
    approved_by = Column(
        String,
        nullable=True
    )

    approved_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    # "manual" for user-created risks, "auto" for risks the engine
    # derives from an asset's vulnerabilities. Lets the generator find
    # and update its own risk for an asset without touching manual ones.
    source = Column(
        String,
        nullable=False,
        server_default=text("'manual'")
    )

    org_id = Column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
        index=True
    )

    # User accountable for treatment. Distinct from `owner` above,
    # which is free text (e.g. an asset's owner label) - assignee_id
    # is a real user reference.
    assignee_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )

    # SLA due date, computed once at creation from risk_level and
    # never silently recomputed on a later edit.
    due_date = Column(
        DateTime(timezone=True),
        nullable=True
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

    assignee = relationship("User", foreign_keys=[assignee_id])

    evidence = relationship(
        "EvidenceAttachment",
        back_populates="risk",
        cascade="all, delete-orphan"
    )

    treatment_history = relationship(
        "RiskTreatmentHistory",
        back_populates="risk",
        cascade="all, delete-orphan"
    )