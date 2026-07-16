"""
CyberRisk360

Purpose:
Check whether a CVE is in CISA's Known Exploited Vulnerabilities (KEV)
catalog. Unlike NVD/plugin enrichment (one lookup per CVE), KEV is a
single bulk JSON feed - the whole catalog is cached locally and
refreshed as a unit on a TTL, then individual CVEs are checked against
the local cache with no per-check network call. Mirrors
cve_enrichment.py's retry/backoff shape for the one fetch this module
does make.
"""

import time
from datetime import datetime, timedelta, timezone

import requests

from app.repositories.enrichment.cisa_kev_repository import (
    get_by_cve,
    get_latest_fetch_time,
    replace_catalog,
)

_KEV_FEED_URL = (
    "https://www.cisa.gov/sites/default/files/feeds/"
    "known_exploited_vulnerabilities.json"
)

# How long a cached catalog pull is trusted before refreshing again.
# CISA updates the feed as new vulnerabilities are confirmed exploited,
# not on a fixed schedule - daily is frequent enough for this use case
# without refetching a ~1-2MB feed on every lookup.
CATALOG_TTL = timedelta(hours=24)

_MAX_ATTEMPTS = 3
_BASE_BACKOFF_SECONDS = 1


def _parse_date(value):
    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed


def _fetch_catalog():
    """
    Fetch and parse the whole KEV feed, retrying with exponential
    backoff on transient failures (timeouts, connection errors, 5xx,
    429 - honoring Retry-After when present). Returns a list of entry
    dicts, or None if every attempt failed.
    """

    for attempt in range(_MAX_ATTEMPTS):

        try:
            response = requests.get(_KEV_FEED_URL, timeout=30)
        except requests.RequestException:
            response = None

        if response is not None and response.status_code == 200:
            payload = response.json()

            return [
                {
                    "cve_id": item["cveID"],
                    "vulnerability_name": item.get("vulnerabilityName"),
                    "date_added": _parse_date(item.get("dateAdded")),
                    "due_date": _parse_date(item.get("dueDate")),
                    "required_action": item.get("requiredAction"),
                    "known_ransomware_use": item.get("knownRansomwareCampaignUse"),
                    "notes": item.get("notes"),
                }
                for item in payload.get("vulnerabilities", [])
            ]

        transient = (
            response is None
            or response.status_code == 429
            or response.status_code >= 500
        )

        if not transient:
            return None

        if attempt < _MAX_ATTEMPTS - 1:

            retry_after = (
                response.headers.get("Retry-After")
                if response is not None and response.status_code == 429
                else None
            )

            if retry_after is not None:
                try:
                    time.sleep(float(retry_after))
                    continue
                except ValueError:
                    pass

            time.sleep(_BASE_BACKOFF_SECONDS * (2 ** attempt))

    return None


def _is_stale(fetched_at) -> bool:
    if fetched_at is None:
        return True

    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=timezone.utc)

    return datetime.now(timezone.utc) - fetched_at >= CATALOG_TTL


def _refresh_if_stale(db):
    if not _is_stale(get_latest_fetch_time(db)):
        return

    entries = _fetch_catalog()

    if entries is not None:
        replace_catalog(db, entries, datetime.now(timezone.utc))


def check_kev_status(db, cve_id: str):
    """
    Return this CVE's KEV status. Refreshes the local catalog cache
    first if it's stale or empty - a network failure during refresh
    just means the (possibly stale, possibly empty) existing cache is
    used, rather than the whole check failing.
    """

    if not cve_id:
        return {"in_kev": False}

    _refresh_if_stale(db)

    entry = get_by_cve(db, cve_id)

    if not entry:
        return {"in_kev": False}

    return {
        "in_kev": True,
        "vulnerability_name": entry.vulnerability_name,
        "date_added": entry.date_added,
        "due_date": entry.due_date,
        "required_action": entry.required_action,
        "known_ransomware_use": entry.known_ransomware_use,
    }
