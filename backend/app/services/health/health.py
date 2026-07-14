"""
CyberRisk360

Purpose:
Readiness checks for the /ready endpoint: can we reach the database,
and is its schema migrated to the latest Alembic revision?

The migration check exists so a schema that is behind head surfaces as
a clear, boot-time-style readiness failure ("db behind head, run alembic
upgrade") instead of an opaque 500 the first time a request touches a
missing table.
"""

from sqlalchemy import text

from app.core.constants import BACKEND_DIR


def _expected_head():
    """
    The latest migration revision defined in alembic/versions, or None
    if it can't be resolved (Alembic misconfigured / unavailable).
    """

    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        config = Config(str(BACKEND_DIR / "alembic.ini"))
        script = ScriptDirectory.from_config(config)

        return script.get_current_head()

    except Exception:
        return None


def _current_revision(db):
    """
    The revision the connected database is stamped at, or None if the
    alembic_version table is absent (never migrated).
    """

    try:
        row = db.execute(
            text("SELECT version_num FROM alembic_version")
        ).first()

        return row[0] if row else None

    except Exception:
        return None


def check_readiness(db):
    """
    Return `(ready: bool, detail: dict)` describing database
    connectivity and migration state.
    """

    detail = {
        "database": "unknown",
        "migration": "unknown",
    }

    # 1. Connectivity.
    try:
        db.execute(text("SELECT 1"))
        detail["database"] = "ok"
    except Exception:
        detail["database"] = "unreachable"
        return False, detail

    # 2. Migration state.
    head = _expected_head()
    current = _current_revision(db)

    detail["current_revision"] = current
    detail["head_revision"] = head

    if head is None:
        # Can't determine head; don't fail readiness on connectivity
        # alone, but flag it.
        detail["migration"] = "unknown"
        return True, detail

    if current == head:
        detail["migration"] = "up-to-date"
        return True, detail

    detail["migration"] = "behind"
    return False, detail
