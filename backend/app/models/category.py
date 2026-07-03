"""
CyberRisk360

Purpose:
Stores categories within
compliance frameworks.
"""

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String

from sqlalchemy.orm import relationship

from app.db.database import Base


class Category(Base):
    """
    Compliance framework category.

    Examples

    NIST:
        PR.AC
        ID.AM

    ISO:
        A.5
        A.6

    CIS:
        IG1
    """

    __tablename__ = "categories"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    framework_id = Column(
        Integer,
        ForeignKey("frameworks.id"),
        nullable=False
    )

    category_code = Column(
        String,
        nullable=False
    )

    name = Column(
        String,
        nullable=False
    )

    description = Column(
        String,
        nullable=True
    )

    framework = relationship(
        "Framework",
        back_populates="categories"
    )

    controls = relationship(
        "Control",
        back_populates="category",
        cascade="all, delete-orphan"
    )