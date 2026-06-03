"""
CyberRisk360

Purpose:
Stores security controls from
various compliance frameworks.
"""

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from app.database import Base


class Control(Base):
    """
    Security control register.

    Examples:

    ISO27001 A.8.2
    NIST PR.AC-1
    OWASP ASVS V5
    CIS Control 1
    """

    __tablename__ = "controls"

    # Unique database identifier
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Framework control identifier
    control_id = Column(
        String,
        nullable=False,
        unique=True
    )

    # Control name
    name = Column(
        String,
        nullable=False
    )

    # Control description
    description = Column(
        String,
        nullable=False
    )

    # Compliance framework
    framework = Column(
        String,
        nullable=False
    )

    # Implementation status
    status = Column(
        String,
        default="Missing"
    )