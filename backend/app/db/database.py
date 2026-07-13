"""
CyberRisk360

Purpose:
Configure database connection and SQLAlchemy session management.

Reads DATABASE_URL from the environment so the same code path works
against SQLite (zero-config local default) and PostgreSQL (set
DATABASE_URL, e.g. postgresql+psycopg://user:pass@host:5432/db).
Alembic (alembic/env.py) reuses this module's `engine`/`DATABASE_URL`/
`Base` directly rather than duplicating connection logic, so this is
the single place that ever decides how the app connects to its
database.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.constants import BACKEND_DIR

# Populates os.environ from a local .env file if present; never
# overrides a variable that's already set (e.g. by Docker/the shell),
# so real environment configuration always wins.
load_dotenv()

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"sqlite:///{BACKEND_DIR / 'cyberrisk360.db'}"
)

_is_sqlite = DATABASE_URL.startswith("sqlite")

# check_same_thread=False is required for SQLite with FastAPI, but
# Postgres drivers reject the kwarg outright.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    pool_pre_ping=True
)

if _is_sqlite:

    @event.listens_for(engine, "connect")
    def _configure_sqlite_connection(dbapi_connection, connection_record):
        """
        SQLite ignores FOREIGN KEY constraints unless explicitly told
        to enforce them per-connection. PostgreSQL enforces them
        natively, so this only runs for SQLite.

        Also enables WAL mode (readers don't block on a writer, and
        vice versa - standard SQLite web-app hardening) and a busy
        timeout (bounds how long a genuinely concurrent writer from a
        different request waits before failing, instead of failing
        immediately). Note this does NOT help two connections used
        sequentially within the same thread/request (e.g. one with an
        open uncommitted transaction, then another trying to write) -
        there's nothing else running to release the first connection's
        lock while the second waits, so that case will still wait out
        the full timeout and fail. That's why
        services/enrichment/plugin_enrichment.py shares its caller's
        session instead of opening its own - see that module's
        docstring for the full story.
        """

        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

# Standard Alembic-recommended naming convention: without it,
# autogenerate produces unnamed/differently-named constraints across
# dialects, making future migration diffs noisy and unstable.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Database session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class inherited by all SQLAlchemy models
Base = declarative_base(
    metadata=MetaData(naming_convention=NAMING_CONVENTION)
)
