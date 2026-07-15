"""
CyberRisk360

Purpose:
Enrich CVE IDs (already known from plugin enrichment - see
plugin_enrichment.py) with CVSS vector/version, CWE, description, and
published date from the NVD (National Vulnerability Database) REST
API, backed by a persistent cache with retry/backoff on transient
network failures. Mirrors plugin_enrichment.py's structure/contract.
"""

import time
from datetime import datetime, timedelta, timezone

import requests

from app.core.config import NVD_API_KEY

from app.repositories.enrichment.nvd_cache_repository import (
    get_cache_entry,
    save_success,
    save_failure
)

# Same rationale as plugin_enrichment.py's FAILURE_RETRY_TTL: avoid
# hammering NVD for a cve_id it reliably has no record of, while still
# recovering from a transient outage without a code change.
FAILURE_RETRY_TTL = timedelta(hours=24)

_MAX_ATTEMPTS = 3
_BASE_BACKOFF_SECONDS = 1

_NVD_CVE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

# NVD's rate window is 30 seconds; the request budget within it
# depends on whether an API key is present.
_RATE_WINDOW_SECONDS = 30.0
_MAX_REQUESTS_UNAUTHENTICATED = 5
_MAX_REQUESTS_WITH_KEY = 50

_last_request_at = None

_EMPTY_RESULT = {
    "cvss_score": None,
    "cvss_vector": None,
    "cvss_version": None,
    "cwe_id": None,
    "description": "",
    "published_at": None,
}


def _throttle():
    """
    Enforce a fixed interval between NVD requests within this process.
    Callers enrich one CVE at a time inside the same sequential import
    loop that also does plugin enrichment, so a fixed-interval spacing
    is enough - no concurrent callers to coordinate via a token bucket.
    """

    global _last_request_at

    max_requests = (
        _MAX_REQUESTS_WITH_KEY if NVD_API_KEY
        else _MAX_REQUESTS_UNAUTHENTICATED
    )
    min_interval = _RATE_WINDOW_SECONDS / max_requests

    now = time.monotonic()

    if _last_request_at is not None:
        elapsed = now - _last_request_at
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)

    _last_request_at = time.monotonic()


def _fetch_cve(cve_id: str):
    """
    Fetch parsed NVD JSON for one CVE, retrying with exponential
    backoff on transient failures (timeouts, connection errors, 5xx,
    429 - honoring Retry-After when present). A non-transient failure
    (malformed id, or NVD having no record of an otherwise
    well-formed id - a 200 with an empty result) is not retried.
    """

    headers = {"apiKey": NVD_API_KEY} if NVD_API_KEY else {}
    params = {"cveId": cve_id}

    for attempt in range(_MAX_ATTEMPTS):

        _throttle()

        try:
            response = requests.get(
                _NVD_CVE_URL, headers=headers, params=params, timeout=10
            )
        except requests.RequestException:
            response = None

        if response is not None and response.status_code == 200:
            payload = response.json()

            if not payload.get("vulnerabilities"):
                # Well-formed request, no matching record - not
                # transient, retrying won't help.
                return None

            return payload

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


def _extract_cvss(cve: dict):
    metrics = cve.get("metrics", {})

    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        entries = metrics.get(key)

        if entries:
            cvss_data = entries[0].get("cvssData", {})

            return (
                cvss_data.get("baseScore"),
                cvss_data.get("vectorString"),
                cvss_data.get("version"),
            )

    return None, None, None


def _extract_cwe(cve: dict):
    for weakness in cve.get("weaknesses", []):
        for description in weakness.get("description", []):

            value = description.get("value", "")

            # Skips NVD's own "no info"/"other" placeholders - a real
            # CWE id always starts with "CWE-".
            if value.startswith("CWE-"):
                return value

    return None


def _extract_description(cve: dict):
    for description in cve.get("descriptions", []):
        if description.get("lang") == "en":
            return description.get("value", "")

    return ""


def _extract_published(cve: dict):
    published = cve.get("published")

    if not published:
        return None

    try:
        published_at = datetime.fromisoformat(published)
    except ValueError:
        return None

    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)

    return published_at


def _parse_nvd_response(payload: dict):
    cve = payload["vulnerabilities"][0]["cve"]

    cvss_score, cvss_vector, cvss_version = _extract_cvss(cve)

    return {
        "cvss_score": cvss_score,
        "cvss_vector": cvss_vector,
        "cvss_version": cvss_version,
        "cwe_id": _extract_cwe(cve),
        "description": _extract_description(cve),
        "published_at": _extract_published(cve),
    }


def enrich_cve(db, cve_id: str):
    """
    Return (result_dict, cache_written) for a cve_id, checking the
    persistent cache before ever making a network call. Same contract
    as get_plugin_enrichment (see its docstring for the full
    rationale): cache_written is True only when this call actually
    made a fetch attempt (success or failure) - False on a cache hit
    or a cached-failure-within-TTL - so the caller knows whether a
    commit is needed.

    Takes the caller's db session and only flushes, never commits -
    same reasoning as get_plugin_enrichment (avoids a second
    connection writing the cache table while the caller's own
    transaction is still open, which reliably deadlocks on SQLite).
    """

    entry = get_cache_entry(db, cve_id)

    if entry and entry.status == "ok":

        return {
            "cvss_score": entry.cvss_score,
            "cvss_vector": entry.cvss_vector,
            "cvss_version": entry.cvss_version,
            "cwe_id": entry.cwe_id,
            "description": entry.description,
            "published_at": entry.published_at,
        }, False

    if entry and entry.status == "failed":

        fetched_at = entry.fetched_at

        # SQLite doesn't reliably round-trip tzinfo - always written
        # as UTC, so naive means UTC.
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=timezone.utc)

        age = datetime.now(timezone.utc) - fetched_at

        if age < FAILURE_RETRY_TTL:
            return dict(_EMPTY_RESULT), False

    payload = _fetch_cve(cve_id)

    if not payload:

        save_failure(db, cve_id)

        return dict(_EMPTY_RESULT), True

    result = _parse_nvd_response(payload)

    save_success(
        db,
        cve_id,
        result["cvss_score"],
        result["cvss_vector"],
        result["cvss_version"],
        result["cwe_id"],
        result["description"],
        result["published_at"],
    )

    return result, True
