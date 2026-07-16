from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.epss_score_cache import EpssScoreCache


def get_cache_entry(
    db: Session,
    cve_id: str
):
    return (
        db.query(EpssScoreCache)
        .filter(
            EpssScoreCache.cve_id == cve_id
        )
        .first()
    )


def save_success(
    db: Session,
    cve_id: str,
    epss_score: float,
    percentile: float,
    score_date: str
):
    entry = get_cache_entry(db, cve_id)

    if not entry:
        entry = EpssScoreCache(cve_id=cve_id)
        db.add(entry)

    entry.epss_score = epss_score
    entry.percentile = percentile
    entry.score_date = score_date
    entry.status = "ok"
    entry.fetched_at = datetime.now(timezone.utc)

    # Flush (not commit) - shares the caller's transaction, same
    # convention as nvd_cache_repository.py.
    db.flush()

    return entry


def save_failure(
    db: Session,
    cve_id: str
):
    entry = get_cache_entry(db, cve_id)

    if not entry:
        entry = EpssScoreCache(cve_id=cve_id)
        db.add(entry)

    entry.status = "failed"
    entry.fetched_at = datetime.now(timezone.utc)

    db.flush()

    return entry
