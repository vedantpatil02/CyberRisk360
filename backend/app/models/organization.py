"""
CyberRisk360

Purpose:
Tenant boundary. Every per-organization record (users, assets,
vulnerabilities, risks, mappings, audit logs) carries an `org_id`
pointing here; reference data (frameworks/controls) is shared across
organizations and is deliberately NOT scoped.
"""

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy.sql import func

from app.db.database import Base


class Organization(Base):

    __tablename__ = "organizations"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String,
        nullable=False
    )

    # URL/identifier-friendly unique handle for the org.
    slug = Column(
        String,
        nullable=False,
        unique=True,
        index=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
