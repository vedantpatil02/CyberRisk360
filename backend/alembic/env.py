import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context

# backend/alembic/env.py -> backend/
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

# Reuse the app's own engine/URL/Base rather than duplicating
# connection logic or hardcoding credentials in alembic.ini - this is
# the same engine the running app uses (same dialect-conditional
# connect_args, pool_pre_ping, SQLite FK-enforcement PRAGMA), so
# migrations behave identically to the app.
from app.db.database import DATABASE_URL, engine, Base
import app.models  # noqa: F401 - registers all models on Base.metadata

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Uses the app's actual engine (app.db.database.engine) instead of
    building a fresh one from alembic.ini, so migrations always see
    the same DATABASE_URL and dialect-specific behavior as the app.
    """

    with engine.connect() as connection:

        # The app engine enables SQLite FK enforcement on every
        # connection. That breaks batch migrations, which recreate a
        # table by dropping the original - if another table references
        # it by FK, the DROP is rejected. Disable enforcement for the
        # migration run (issued on the raw DBAPI connection, before any
        # transaction, so the PRAGMA actually takes effect). It is
        # restored automatically on the next (app) connection.
        if connection.dialect.name == "sqlite":
            raw_connection = connection.connection
            cursor = raw_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=OFF")
            cursor.close()

        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
