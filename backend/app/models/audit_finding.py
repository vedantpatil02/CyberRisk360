"""
CyberRisk360

Purpose:
Individual observation recorded during an audit engagement. May
optionally reference the specific control it concerns.
"""

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class AuditFinding(Base):

    __tablename__ = "audit_findings"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    audit_id = Column(
        Integer,
        ForeignKey("audits.id"),
        nullable=False,
        index=True
    )

    control_id = Column(
        Integer,
        ForeignKey("controls.id"),
        nullable=True
    )

    title = Column(
        String,
        nullable=False
    )

    description = Column(
        String,
        nullable=True
    )

    # Critical / High / Medium / Low - same vocabulary as
    # Vulnerability.severity / Risk.risk_level.
    severity = Column(
        String,
        nullable=False,
        default="Medium"
    )

    # Open / Remediated / Accepted / Closed
    status = Column(
        String,
        nullable=False,
        default="Open"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    audit = relationship(
        "Audit",
        back_populates="findings"
    )

    control = relationship("Control")
