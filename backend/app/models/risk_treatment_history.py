"""
CyberRisk360

Purpose:
Audit trail of risk treatment lifecycle events (proposed, approved,
rejected) - same shape as MappingHistory, for the risk treatment/
approval workflow instead of vulnerability-control mappings.
"""

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class RiskTreatmentHistory(Base):

    __tablename__ = "risk_treatment_history"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    risk_id = Column(
        Integer,
        ForeignKey(
            "risks.id"
        ),
        nullable=False
    )

    # proposed / approved / rejected
    action = Column(
        String,
        nullable=False
    )

    previous_status = Column(
        String,
        nullable=True
    )

    new_status = Column(
        String,
        nullable=False
    )

    # mitigate / accept / transfer / avoid
    treatment_type = Column(
        String,
        nullable=True
    )

    # Reviewer/proposer identity
    actor = Column(
        String,
        nullable=True
    )

    note = Column(
        String,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    org_id = Column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False,
        index=True
    )

    risk = relationship(
        "Risk",
        back_populates="treatment_history"
    )
