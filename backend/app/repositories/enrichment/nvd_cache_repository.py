from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.nvd_enrichment_cache import NvdEnrichmentCache


def get_cache_entry(
    db: Session,
    cve_id: str
):
    return (
        db.query(NvdEnrichmentCache)
        .filter(
            NvdEnrichmentCache.cve_id == cve_id
        )
        .first()
    )


def save_success(
    db: Session,
    cve_id: str,
    cvss_score: float,
    cvss_vector: str,
    cvss_version: str,
    cwe_id: str,
    description: str,
    published_at
):
    entry = get_cache_entry(db, cve_id)

    if not entry:
        entry = NvdEnrichmentCache(cve_id=cve_id)
        db.add(entry)

    entry.cvss_score = cvss_score
    entry.cvss_vector = cvss_vector
    entry.cvss_version = cvss_version
    entry.cwe_id = cwe_id
    entry.description = description
    entry.published_at = published_at
    entry.status = "ok"
    entry.fetched_at = datetime.now(timezone.utc)

    # Flush (not commit) - shares the caller's transaction, same
    # convention as plugin_cache_repository.py.
    db.flush()

    return entry


def save_failure(
    db: Session,
    cve_id: str
):
    entry = get_cache_entry(db, cve_id)

    if not entry:
        entry = NvdEnrichmentCache(cve_id=cve_id)
        db.add(entry)

    entry.status = "failed"
    entry.fetched_at = datetime.now(timezone.utc)

    db.flush()

    return entry
