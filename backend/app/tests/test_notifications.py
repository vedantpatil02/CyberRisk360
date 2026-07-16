"""
CyberRisk360

Purpose:
Tests for the in-app notification list (evidence expiry) - computed
live at read time, no background job. Expired vs. expiring-soon vs.
far-future/no-expiry buckets, and org isolation.
"""

import io
from datetime import datetime, timedelta, timezone

from app.core.constants import ROLE_ADMIN
from app.models.organization import Organization
from app.repositories.users.user_repository import create_user

ORG1 = 1
ORG2 = 2


def _create_asset(client):
    response = client.post("/assets", json={
        "name": "web-01", "asset_type": "server", "owner": "IT",
        "criticality": "High", "ip_address": "10.0.0.5",
        "environment": "prod"
    })
    assert response.status_code == 200
    return client.get("/assets").json()[0]["id"]


def _create_risk(client, asset_id, **overrides):
    payload = {
        "title": "Risk 1", "description": "d", "asset_id": asset_id,
        "impact": 3, "likelihood": 3, "owner": "IT"
    }
    payload.update(overrides)
    response = client.post("/risks", json=payload)
    assert response.status_code == 200
    return client.get("/risks").json()[-1]["id"]


def _make_uploader(db):
    # The test client's default authenticated identity is
    # "test@example.com" - a real matching User row is required since
    # uploaded_by_id is a NOT NULL FK.
    return create_user(
        db, username="test@example.com", email="test@example.com",
        password="x", role=ROLE_ADMIN, org_id=ORG1
    )


def _make_org2(db):
    db.add(Organization(id=ORG2, name="Second Org", slug="second"))
    db.commit()


def _upload_evidence(client, risk_id, expires_at=None):
    data = {}
    if expires_at is not None:
        data["expires_at"] = expires_at.isoformat()

    response = client.post(
        f"/risks/{risk_id}/evidence",
        files={"file": ("proof.txt", io.BytesIO(b"data"), "text/plain")},
        data=data,
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_expired_evidence_shows_as_notification(client, db_session):
    _make_uploader(db_session)
    asset_id = _create_asset(client)
    risk_id = _create_risk(client, asset_id)
    past = datetime.now(timezone.utc) - timedelta(days=1)
    _upload_evidence(client, risk_id, expires_at=past)

    response = client.get("/notifications")

    assert response.status_code == 200
    notifications = response.json()
    assert len(notifications) == 1
    assert notifications[0]["type"] == "evidence_expired"
    assert notifications[0]["entity_type"] == "risk"
    assert notifications[0]["entity_id"] == risk_id


def test_evidence_expiring_soon_shows_as_notification(client, db_session):
    _make_uploader(db_session)
    asset_id = _create_asset(client)
    risk_id = _create_risk(client, asset_id)
    soon = datetime.now(timezone.utc) + timedelta(days=5)
    _upload_evidence(client, risk_id, expires_at=soon)

    response = client.get("/notifications")

    assert response.status_code == 200
    notifications = response.json()
    assert len(notifications) == 1
    assert notifications[0]["type"] == "evidence_expiring_soon"


def test_far_future_expiry_is_not_a_notification(client, db_session):
    _make_uploader(db_session)
    asset_id = _create_asset(client)
    risk_id = _create_risk(client, asset_id)
    far_future = datetime.now(timezone.utc) + timedelta(days=365)
    _upload_evidence(client, risk_id, expires_at=far_future)

    response = client.get("/notifications")

    assert response.status_code == 200
    assert response.json() == []


def test_evidence_without_expiry_is_not_a_notification(client, db_session):
    _make_uploader(db_session)
    asset_id = _create_asset(client)
    risk_id = _create_risk(client, asset_id)
    _upload_evidence(client, risk_id)

    response = client.get("/notifications")

    assert response.status_code == 200
    assert response.json() == []


def test_notifications_are_isolated_by_org(client, db_session, as_user):
    _make_org2(db_session)
    _make_uploader(db_session)

    as_user(role=ROLE_ADMIN, org_id=ORG1, sub="test@example.com")
    asset_id = _create_asset(client)
    risk_id = _create_risk(client, asset_id)
    past = datetime.now(timezone.utc) - timedelta(days=1)
    _upload_evidence(client, risk_id, expires_at=past)

    as_user(role=ROLE_ADMIN, org_id=ORG2, sub="test@example.com")
    response = client.get("/notifications")

    assert response.status_code == 200
    assert response.json() == []


def test_notifications_sorted_soonest_first(client, db_session):
    _make_uploader(db_session)
    asset_id = _create_asset(client)
    risk_id = _create_risk(client, asset_id)

    later = datetime.now(timezone.utc) + timedelta(days=10)
    sooner = datetime.now(timezone.utc) + timedelta(days=2)
    _upload_evidence(client, risk_id, expires_at=later)
    _upload_evidence(client, risk_id, expires_at=sooner)

    response = client.get("/notifications")

    notifications = response.json()
    assert len(notifications) == 2
    assert notifications[0]["expires_at"] < notifications[1]["expires_at"]
