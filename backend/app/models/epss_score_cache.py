"""
CyberRisk360

Purpose:
Persistent cache of FIRST.org EPSS (Exploit Prediction Scoring System)
lookups, keyed by cve_id. Mirrors nvd_enrichment_cache.py's shape, with
one deliberate difference: EPSS scores are recomputed daily, so even a
"ok" entry needs a TTL (enforced in services/enrichment/epss_enrichment.py,
not here - this table just stores what was last fetched and when).
"""

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import DateTime
from sqlalchemy.sql import func

from app.db.database import Base


class EpssScoreCache(Base):

    __tablename__ = "epss_score_cache"

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

    epss_score = Column(
        Float,
        nullable=True
    )

    percentile = Column(
        Float,
        nullable=True
    )

    # The date FIRST.org computed the score - informational only, not
    # used for freshness (fetched_at drives that).
    score_date = Column(
        String,
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
