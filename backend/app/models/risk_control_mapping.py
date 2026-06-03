"""
CyberRisk360

Purpose:
Maps risks to mitigating controls.
"""

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import ForeignKey

from app.database import Base


class RiskControlMapping(Base):
    """
    Many-to-many relationship
    between risks and controls.
    """

    __tablename__ = (
        "risk_control_mappings"
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    risk_id = Column(
        Integer,
        ForeignKey("risks.id"),
        nullable=False
    )

    control_id = Column(
        Integer,
        ForeignKey("controls.id"),
        nullable=False
    )