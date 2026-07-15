"""
CyberRisk360

Purpose:
Persistent cache of NVD (National Vulnerability Database) CVE lookups
(CVSS vector/version, CWE, description, published date), keyed by
cve_id. Mirrors plugin_enrichment_cache.py's shape/lifecycle - a
separate table because the key and payload shape genuinely differ
(cve_id vs plugin_id; CVSS vector/CWE/published date vs none of
that), not because the two enrichment sources are otherwise related.
"""

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import Text
from sqlalchemy import DateTime
from sqlalchemy.sql import func

from app.db.database import Base


class NvdEnrichmentCache(Base):

    __tablename__ = "nvd_enrichment_cache"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    cve_id = Column(
        String,
        nullable=False,
        unique=True,
        index=True
    )

    cvss_score = Column(
        Float,
        nullable=True
    )

    cvss_vector = Column(
        String,
        nullable=True
    )

    cvss_version = Column(
        String,
        nullable=True
    )

    cwe_id = Column(
        String,
        nullable=True
    )

    description = Column(
        Text,
        nullable=True
    )

    published_at = Column(
        DateTime(timezone=True),
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
