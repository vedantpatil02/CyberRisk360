"""
CyberRisk360

Purpose:
Local cache of CISA's Known Exploited Vulnerabilities (KEV) catalog -
a single bulk JSON feed (no per-CVE endpoint), so the whole catalog is
cached and refreshed as a unit (app/services/enrichment/cisa_kev.py)
rather than looked up per-CVE over the network like NVD/plugin
enrichment.
"""

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import DateTime
from sqlalchemy.sql import func

from app.db.database import Base


class CisaKevEntry(Base):

    __tablename__ = "cisa_kev_entries"

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

    vulnerability_name = Column(
        String,
        nullable=True
    )

    date_added = Column(
        DateTime(timezone=True),
        nullable=True
    )

    due_date = Column(
        DateTime(timezone=True),
        nullable=True
    )

    required_action = Column(
        Text,
        nullable=True
    )

    # CISA's knownRansomwareCampaignUse - "Known" or "Unknown".
    known_ransomware_use = Column(
        String,
        nullable=True
    )

    notes = Column(
        Text,
        nullable=True
    )

    # Shared by every row from the same catalog pull - lets the
    # service know when the whole catalog needs refreshing without a
    # separate "catalog metadata" table.
    fetched_at = Column(
        DateTime(timezone=True),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
