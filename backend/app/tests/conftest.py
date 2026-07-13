"""
CyberRisk360

Purpose:
Shared pytest fixtures: an isolated in-memory database and a
FastAPI TestClient with auth/db dependencies overridden.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
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


def override_get_current_user():
    return {
        "sub": "test@example.com",
        "role": ROLE_ADMIN
    }


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    try:
        yield session

    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    with TestClient(app) as test_client:
        yield test_client
