"""
CyberRisk360

Purpose:
Persistent cache of Nessus Plugin ID enrichment lookups (CVE IDs,
description, solution), so a process restart doesn't lose everything
and repeated imports of the same findings don't re-scrape tenable.com.
"""

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import DateTime
from sqlalchemy.sql import func

from app.db.database import Base


class PluginEnrichmentCache(Base):

    __tablename__ = "plugin_enrichment_cache"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    plugin_id = Column(
        String,
        nullable=False,
        unique=True,
        index=True
    )

    cve_ids = Column(
        String,
        nullable=True
    )

    description = Column(
        Text,
        nullable=True
    )

    solution = Column(
        Text,
        nullable=True
    )

    # "ok" or "failed"
    status = Column(
        String,
        nullable=False
    )

    fetched_at = Column(
        DateTime(timezone=True),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
