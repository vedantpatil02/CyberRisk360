"""
CyberRisk360

Purpose:
Stores organizational risks and their
associated business impact.
"""

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import ForeignKey
from sqlalchemy import text

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

    # Open / Mitigated / Accepted / Closed
    status = Column(
        String,
        default="Open"
    )

    # "manual" for user-created risks, "auto" for risks the engine
    # derives from an asset's vulnerabilities. Lets the generator find
    # and update its own risk for an asset without touching manual ones.
    source = Column(
        String,
        nullable=False,
        server_default=text("'manual'")
    )