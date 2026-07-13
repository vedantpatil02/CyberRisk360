"""
CyberRisk360

Purpose:
Audit trail of vulnerability-control mapping lifecycle events
(created, approved, rejected) for compliance traceability.
"""

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class MappingHistory(Base):

    __tablename__ = "mapping_history"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    mapping_id = Column(
        Integer,
        ForeignKey(
            "vulnerability_control_mappings.id"
        ),
        nullable=False
    )

    # created / approved / rejected
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

    # Reviewer identity, or "system" for engine-generated events
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

    mapping = relationship(
        "VulnerabilityControlMapping",
        back_populates="history"
    )
