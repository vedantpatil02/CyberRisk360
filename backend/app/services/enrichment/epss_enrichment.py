"""
CyberRisk360

Purpose:
Look up a CVE's EPSS (Exploit Prediction Scoring System) score - the
probability it will be exploited in the wild in the next 30 days, plus
its percentile rank - from FIRST.org's public API, backed by a
persistent cache with retry/backoff on transient network failures.
Mirrors cve_enrichment.py's structure, with one deliberate difference:
EPSS scores are recomputed daily, so a successful cache entry still
expires (SCORE_TTL) - cve_enrichment.py's NVD data (CVSS/CWE/
description) is immutable once published and never re-fetched.
"""

import time
from datetime import datetime, timedelta, timezone

import requests

from app.repositories.enrichment.epss_cache_repository import (
    get_cache_entry,
    save_success,
    save_failure
)

SCORE_TTL = timedelta(hours=24)
FAILURE_RETRY_TTL = timedelta(hours=24)

_MAX_ATTEMPTS = 3
_BASE_BACKOFF_SECONDS = 1

_EPSS_URL = "https://api.first.org/data/v1/epss"


def _fetch_epss(cve_id: str):
    """
    Fetch parsed EPSS JSON for one CVE, retrying with exponential
    backoff on transient failures (timeouts, connection errors, 5xx,
    429 - honoring Retry-After when present). A non-transient failure
    (FIRST.org having no EPSS record for an otherwise well-formed id -
    a 200 with an empty "data" list) is not retried.
    """

    params = {"cve": cve_id}

    for attempt in range(_MAX_ATTEMPTS):

        try:
            response = requests.get(_EPSS_URL, params=params, timeout=10)
        except requests.RequestException:
            response = None

        if response is not None and response.status_code == 200:
            payload = response.json()

            data = payload.get("data")

            if not data:
                # Well-formed request, no matching record - not
                # transient, retrying won't help.
                return None

            return data[0]

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


def _parse_epss_entry(entry: dict):
    return {
        "epss_score": float(entry["epss"]),
        "percentile": float(entry["percentile"]),
        "date": entry.get("date"),
    }


def get_epss_score(db, cve_id: str):
    """
    Return {"epss_score", "percentile", "date"} for a cve_id, or None
    if there's no cve_id, no network record, or a cached failure still
    within its retry backoff. Checks the persistent cache before ever
    making a network call.

    Unlike enrich_cve's "ok" entries (trusted forever), a "ok" entry
    here is only reused within SCORE_TTL - EPSS scores are recomputed
    daily, so a stale cache entry is treated the same as a missing one.
    """

    if not cve_id:
        return None

    entry = get_cache_entry(db, cve_id)

    if entry:

        fetched_at = entry.fetched_at

        # SQLite doesn't reliably round-trip tzinfo - always written
        # as UTC, so naive means UTC.
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=timezone.utc)

        age = datetime.now(timezone.utc) - fetched_at

        if entry.status == "ok" and age < SCORE_TTL:
            return {
                "epss_score": entry.epss_score,
                "percentile": entry.percentile,
                "date": entry.score_date,
            }

        if entry.status == "failed" and age < FAILURE_RETRY_TTL:
            return None

    raw = _fetch_epss(cve_id)

    if not raw:
        save_failure(db, cve_id)
        return None

    result = _parse_epss_entry(raw)

    save_success(
        db,
        cve_id,
        result["epss_score"],
        result["percentile"],
        result["date"],
    )

    return result
