"""
CyberRisk360

Purpose:
Stores compliance framework
information.
"""

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from sqlalchemy.orm import relationship

from app.db.database import Base


class Framework(Base):
    """
    Compliance framework.

    Examples

    - NIST CSF
    - ISO 27001
    - CIS Controls
    - OWASP ASVS
    """

    __tablename__ = "frameworks"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String,
        nullable=False
    )

    short_name = Column(
        String,
        nullable=False,
        unique=True
    )

    version = Column(
        String,
        nullable=False
    )

    publisher = Column(
        String,
        nullable=False
    )

    description = Column(
        String,
        nullable=True
    )

    release_year = Column(
        Integer,
        nullable=True
    )

    categories = relationship(
        "Category",
        back_populates="framework",
        cascade="all, delete-orphan"
    )