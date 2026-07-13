"""
CyberRisk360

Purpose:
Enrich Nessus Plugin IDs with CVE, description, and solution
information, backed by a persistent cache (survives process restarts,
unlike the old in-memory-only cache) with retry/backoff on transient
network failures.
"""

import re
import time
from datetime import datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup

from app.repositories.enrichment.plugin_cache_repository import (
    get_cache_entry,
    save_success,
    save_failure
)

# How long a failed lookup is trusted before retrying - avoids
# hammering tenable.com for a plugin_id that reliably 404s, while
# still recovering from a transient outage without a code change.
FAILURE_RETRY_TTL = timedelta(hours=24)

_MAX_ATTEMPTS = 3
_BASE_BACKOFF_SECONDS = 1


def _fetch_plugin_page(plugin_id: str):
    """
    Fetch the raw HTML for a plugin page, retrying with exponential
    backoff on transient failures (timeouts, connection errors, 5xx,
    429). A non-transient failure (e.g. 404 - no such plugin page) is
    not retried.
    """

    url = f"https://www.tenable.com/plugins/nessus/{plugin_id}"

    for attempt in range(_MAX_ATTEMPTS):

        try:
            response = requests.get(url, timeout=10)

        except requests.RequestException:
            response = None

        if response is not None and response.status_code == 200:
            return response.text

        transient = (
            response is None
            or response.status_code == 429
            or response.status_code >= 500
        )

        if not transient:
            # e.g. 404 - no such plugin page, retrying won't help.
            return None

        if attempt < _MAX_ATTEMPTS - 1:
            time.sleep(_BASE_BACKOFF_SECONDS * (2 ** attempt))

    return None


def _parse_cve_ids(html: str):

    cves = re.findall(
        r"CVE-\d{4}-\d+",
        html
    )

    if not cves:
        return None

    return ",".join(sorted(set(cves)))


def _parse_description(html: str):

    soup = BeautifulSoup(html, "html.parser")

    meta = soup.find(
        "meta",
        attrs={"name": "description"}
    )

    if meta:
        return meta.get("content", "")

    return ""


def _parse_solution(html: str):

    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text(" ", strip=True)

    if "Solution" not in text:
        return ""

    solution = (
        text.split("Solution")[1]
        .split("Risk Information")[0]
        .strip()
    )

    return solution[:1000]


def get_plugin_enrichment(db, plugin_id: str):
    """
    Return ({"cve_ids", "description", "solution"}, cache_written) for
    a plugin_id, checking the persistent cache before ever making a
    network call. cache_written is True only when this call actually
    wrote the cache (a real fetch attempt happened, success or
    failure) - False on a cache hit. vulnerability_importer.py uses
    this to decide whether a commit is needed: it enriches findings
    ahead of the write transaction and only wants to commit when
    there's something new to make durable, not on every cache hit.

    Takes the caller's db session (same convention as every other
    repository/service in this codebase) and only flushes, never
    commits - an earlier version of this function opened its own
    short-lived session so a successful cache write would survive
    even if the caller's batch later rolled back. That broke on
    SQLite: vulnerability_importer.import_findings holds one
    session/transaction open across the whole finding loop (only
    committing at the end), and a second connection trying to write
    the cache table while that transaction is still open hits
    "database is locked" - reliably, on essentially every
    multi-finding import, since it's the same thread sequentially
    using two connections, not a rare concurrent-request race that a
    busy_timeout could wait out. Sharing the caller's session avoids
    that entirely - the caller is responsible for committing when it
    wants the write durable (see cache_written above).
    """

    entry = get_cache_entry(db, plugin_id)

    if entry and entry.status == "ok":

        return {
            "cve_ids": entry.cve_ids,
            "description": entry.description,
            "solution": entry.solution
        }, False

    if entry and entry.status == "failed":

        fetched_at = entry.fetched_at

        # SQLite doesn't reliably round-trip tzinfo on
        # DateTime(timezone=True) columns - values written as
        # UTC-aware can come back naive. Always written as UTC, so
        # it's safe to assume UTC when it comes back naive.
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=timezone.utc)

        age = datetime.now(timezone.utc) - fetched_at

        if age < FAILURE_RETRY_TTL:

            return {
                "cve_ids": None,
                "description": "",
                "solution": ""
            }, False

    html = _fetch_plugin_page(plugin_id)

    if not html:

        save_failure(db, plugin_id)

        return {
            "cve_ids": None,
            "description": "",
            "solution": ""
        }, True

    result = {
        "cve_ids": _parse_cve_ids(html),
        "description": _parse_description(html),
        "solution": _parse_solution(html)
    }

    save_success(
        db,
        plugin_id,
        result["cve_ids"],
        result["description"],
        result["solution"]
    )

    return result, True
