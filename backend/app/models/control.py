"""
CyberRisk360

Purpose:
Stores security controls
for compliance frameworks.
"""

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String

from sqlalchemy.orm import relationship

from app.db.database import Base


class Control(Base):

    __tablename__ = "controls"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    category_id = Column(
        Integer,
        ForeignKey("categories.id"),
        nullable=False
    )

    control_id = Column(
        String,
        nullable=False,
        unique=True
    )

    title = Column(
        String,
        nullable=False
    )

    description = Column(
        String,
        nullable=False
    )

    implementation_guidance = Column(
        String,
        nullable=True
    )

    priority = Column(
        String,
        default="Medium"
    )

    status = Column(
        String,
        default="Missing"
    )

    category = relationship(
        "Category",
        back_populates="controls"
    )

    vulnerability_mappings = relationship(
        "VulnerabilityControlMapping",
        back_populates="control",
        cascade="all, delete-orphan"
    )