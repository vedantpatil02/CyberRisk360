"""
CyberRisk360

Purpose:
Audit trail of control implementation-status review events - who
reviewed a control, when, what the status changed from/to, and why.
Control.status itself stays a single global/shared field (per-org
control status is a deliberately deferred, separate change - see
docs/ROADMAP.md Phase 4); this only adds a review trail on top of it.
"""

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class ControlReview(Base):

    __tablename__ = "control_reviews"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    control_id = Column(
        Integer,
        ForeignKey("controls.id"),
        nullable=False,
        index=True
    )

    # Reviewer identity from the JWT - same convention as
    # MappingHistory.actor / RiskTreatmentHistory.actor, not a
    # selectable FK.
    reviewer = Column(
        String,
        nullable=True
    )

    previous_status = Column(
        String,
        nullable=True
    )

    new_status = Column(
        String,
        nullable=False
    )

    notes = Column(
        String,
        nullable=True
    )

    # The review *event* belongs to whichever org's user performed it,
    # for audit purposes, even though Control itself is shared
    # reference data.
    org_id = Column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
        index=True
    )

    reviewed_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    control = relationship("Control")
