from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.plugin_enrichment_cache import PluginEnrichmentCache


def get_cache_entry(
    db: Session,
    plugin_id: str
):
    return (
        db.query(PluginEnrichmentCache)
        .filter(
            PluginEnrichmentCache.plugin_id == plugin_id
        )
        .first()
    )


def save_success(
    db: Session,
    plugin_id: str,
    cve_ids: str,
    description: str,
    solution: str
):
    entry = get_cache_entry(db, plugin_id)

    if not entry:
        entry = PluginEnrichmentCache(plugin_id=plugin_id)
        db.add(entry)

    entry.cve_ids = cve_ids
    entry.description = description
    entry.solution = solution
    entry.status = "ok"
    entry.fetched_at = datetime.now(timezone.utc)

    # Flush (not commit) - shares the caller's transaction, same
    # convention as every other repository in this codebase. See
    # services/enrichment/plugin_enrichment.py for why this matters.
    db.flush()

    return entry


def save_failure(
    db: Session,
    plugin_id: str
):
    entry = get_cache_entry(db, plugin_id)

    if not entry:
        entry = PluginEnrichmentCache(plugin_id=plugin_id)
        db.add(entry)

    entry.status = "failed"
    entry.fetched_at = datetime.now(timezone.utc)

    db.flush()

    return entry
