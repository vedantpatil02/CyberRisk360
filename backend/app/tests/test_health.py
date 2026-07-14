"""
CyberRisk360

Tests for the liveness/readiness probes.

The test database is built with `create_all` rather than migrations, so
it has no `alembic_version` row - which is exactly the "schema behind
head" condition /ready is meant to catch. The up-to-date path is
exercised by stamping a matching version row.
"""

from sqlalchemy import text

from app.services.health.health import _expected_head


def test_health_is_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_503_when_schema_behind(client):
    # No alembic_version row in the test DB -> current revision is None,
    # which is behind head.
    response = client.get("/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not ready"
    assert body["database"] == "ok"
    assert body["migration"] == "behind"


def test_ready_ok_when_schema_at_head(client, db_session):
    head = _expected_head()

    db_session.execute(
        text(
            "CREATE TABLE IF NOT EXISTS alembic_version "
            "(version_num VARCHAR(32) NOT NULL)"
        )
    )
    db_session.execute(
        text("INSERT INTO alembic_version (version_num) VALUES (:v)"),
        {"v": head},
    )
    db_session.commit()

    try:
        response = client.get("/ready")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ready"
        assert body["migration"] == "up-to-date"
        assert body["current_revision"] == head
    finally:
        # alembic_version is not a model table, so the db_session
        # fixture won't drop it - clean up to keep tests isolated.
        db_session.execute(text("DROP TABLE alembic_version"))
        db_session.commit()
