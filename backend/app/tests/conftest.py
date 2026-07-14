"""
CyberRisk360

Purpose:
Shared pytest fixtures: an isolated in-memory database and a
FastAPI TestClient with auth/db dependencies overridden.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base
from app.dependencies.database import get_db
from app.dependencies.security import get_current_user
from app.core.constants import ROLE_ADMIN

# app.main already imports app.models, registering them with Base.metadata

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    """
    Same enforcement as app/db/database.py's real engine - without
    this, the test suite would only ever exercise the app-level FK
    existence checks (assets.py/risks.py/vulnerabilities.py/
    controls.py), never the DB-level constraint itself.
    """

    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db

    finally:
        db.close()


DEFAULT_TEST_ORG_ID = 1


def override_get_current_user():
    return {
        "sub": "test@example.com",
        "role": ROLE_ADMIN,
        "org_id": DEFAULT_TEST_ORG_ID
    }


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    # Seed the default organization every per-org row (and the override
    # user's org_id) points at, with slug "default" so open registration
    # resolves it.
    from app.models.organization import Organization
    session.add(
        Organization(
            id=DEFAULT_TEST_ORG_ID,
            name="Test Organization",
            slug="default",
        )
    )
    session.commit()

    try:
        yield session

    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def as_role():
    """
    Temporarily override the authenticated user's role for a single
    test - the only way to exercise RBAC *denial* paths, since the
    default override above always returns admin.
    """

    def _set(role):
        app.dependency_overrides[get_current_user] = lambda: {
            "sub": "test@example.com",
            "role": role,
            "org_id": DEFAULT_TEST_ORG_ID
        }

    yield _set

    app.dependency_overrides[get_current_user] = override_get_current_user


@pytest.fixture()
def as_user():
    """
    Override the authenticated user with a specific role AND org_id -
    the way to exercise cross-organization isolation (a user in org 2
    must not see org 1's data).
    """

    def _set(role=ROLE_ADMIN, org_id=DEFAULT_TEST_ORG_ID, sub="user@example.com"):
        app.dependency_overrides[get_current_user] = lambda: {
            "sub": sub,
            "role": role,
            "org_id": org_id,
        }

    yield _set

    app.dependency_overrides[get_current_user] = override_get_current_user


@pytest.fixture()
def reset_rate_limiter():
    """
    slowapi's Limiter (app/core/rate_limiter.py) uses a single
    process-wide in-memory store, not reset between tests - without
    this, login-rate-limit tests would interfere with each other (and
    with any other test hitting /login) within the same pytest run.
    """

    from app.core.rate_limiter import limiter

    limiter.reset()

    yield

    limiter.reset()


@pytest.fixture()
def seed_asset(client):
    """
    Create a minimal asset and return its id - shared setup needed by
    several test files (assets, dashboard, imports).
    """

    client.post("/assets", json={
        "name": "web-01",
        "asset_type": "server",
        "owner": "IT",
        "criticality": "High",
        "ip_address": "10.0.0.5",
        "environment": "prod"
    })

    return client.get("/assets").json()[0]["id"]
