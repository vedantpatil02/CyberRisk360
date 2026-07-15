"""
CyberRisk360

Purpose:
Tests for the remediation workflow: assignee, due_date/SLA, and
evidence attachments on vulnerabilities and risks.
"""

import io
from datetime import datetime, timedelta, timezone

from app.core.constants import ROLE_ADMIN, ROLE_AUDITOR
from app.models.organization import Organization
from app.repositories.users.user_repository import create_user

ORG1 = 1
ORG2 = 2


def _parse_dt(value):
    # SQLite doesn't reliably round-trip tzinfo - assume UTC if naive,
    # same convention used throughout this codebase.
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


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


def _create_vulnerability(client, asset_id, risk_id, **overrides):
    payload = {
        "title": "t", "description": "d", "asset_id": asset_id,
        "risk_id": risk_id, "cvss_score": 9.5, "owner": "IT"
    }
    payload.update(overrides)
    response = client.post("/vulnerabilities", json=payload)
    assert response.status_code == 200, response.text
    return client.get("/vulnerabilities").json()[-1]["id"]


def _make_user(db, email="assignee@example.com", org_id=ORG1, role=ROLE_ADMIN):
    return create_user(
        db, username=email, email=email, password="x",
        role=role, org_id=org_id
    )


def _make_org2(db):
    db.add(Organization(id=ORG2, name="Second Org", slug="second"))
    db.commit()


# --- due_date / SLA -----------------------------------------------------


def test_vulnerability_due_date_auto_computed_by_severity(client):
    asset_id = _create_asset(client)
    risk_id = _create_risk(client, asset_id)

    before = datetime.now(timezone.utc)
    vulnerability_id = _create_vulnerability(
        client, asset_id, risk_id, cvss_score=9.5  # Critical -> 24h
    )

    due_date = _parse_dt(
        client.get(f"/vulnerabilities/{vulnerability_id}").json()["due_date"]
    )

    expected = before + timedelta(hours=24)
    assert abs((due_date - expected).total_seconds()) < 30


def test_vulnerability_due_date_explicit_overrides_default(client):
    asset_id = _create_asset(client)
    risk_id = _create_risk(client, asset_id)

    explicit = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    vulnerability_id = _create_vulnerability(
        client, asset_id, risk_id, due_date=explicit
    )

    due_date = _parse_dt(
        client.get(f"/vulnerabilities/{vulnerability_id}").json()["due_date"]
    )

    assert abs((due_date - _parse_dt(explicit)).total_seconds()) < 5


def test_vulnerability_update_does_not_shift_due_date(client):
    asset_id = _create_asset(client)
    risk_id = _create_risk(client, asset_id)
    vulnerability_id = _create_vulnerability(
        client, asset_id, risk_id, cvss_score=9.5
    )

    before = client.get(f"/vulnerabilities/{vulnerability_id}").json()["due_date"]

    response = client.put(
        f"/vulnerabilities/{vulnerability_id}", json={"cvss_score": 2.0}
    )
    assert response.status_code == 200

    after = client.get(f"/vulnerabilities/{vulnerability_id}").json()["due_date"]
    assert before == after


def test_risk_regenerate_does_not_reset_due_date(client, db_session):
    asset_id = _create_asset(client)

    from app.repositories.assets.asset_repository import get_asset
    from app.services.risks.risk_generation import generate_risk_for_asset
    from app.repositories.vulnerabilities.vulnerability_repository import (
        create_vulnerability,
    )

    asset = get_asset(db_session, asset_id, org_id=ORG1)
    create_vulnerability(
        db_session, title="f", plugin_id=None, cve_id=None, solution=None,
        ip_address="10.0.0.5", description="d", asset_id=asset_id,
        cvss_score=9.5, severity="Critical", owner="x", status="Open",
        org_id=ORG1,
    )
    db_session.commit()

    risk = generate_risk_for_asset(db_session, asset)
    first_due_date = risk.due_date

    risk_again = generate_risk_for_asset(db_session, asset)
    assert risk_again.due_date == first_due_date


def test_sla_breached_filter_on_vulnerabilities(client):
    asset_id = _create_asset(client)
    risk_id = _create_risk(client, asset_id)

    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    breached_id = _create_vulnerability(
        client, asset_id, risk_id, due_date=past
    )
    _create_vulnerability(client, asset_id, risk_id, due_date=future)

    response = client.get("/vulnerabilities", params={"sla_breached": True})
    assert response.status_code == 200
    ids = [v["id"] for v in response.json()]
    assert ids == [breached_id]

    # A closed vulnerability with a past due_date is not breached.
    client.put(f"/vulnerabilities/{breached_id}", json={"status": "Closed"})
    response = client.get("/vulnerabilities", params={"sla_breached": True})
    assert response.json() == []


def test_sort_by_due_date_is_honored(client):
    asset_id = _create_asset(client)
    risk_id = _create_risk(client, asset_id)

    later = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    sooner = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    later_id = _create_vulnerability(client, asset_id, risk_id, due_date=later)
    sooner_id = _create_vulnerability(client, asset_id, risk_id, due_date=sooner)

    response = client.get(
        "/vulnerabilities", params={"sort_by": "due_date", "order": "asc"}
    )
    ids = [v["id"] for v in response.json()]
    assert ids.index(sooner_id) < ids.index(later_id)


# --- assignee -------------------------------------------------------------


def test_create_vulnerability_with_valid_assignee_succeeds(client, db_session):
    user = _make_user(db_session)
    asset_id = _create_asset(client)
    risk_id = _create_risk(client, asset_id)

    vulnerability_id = _create_vulnerability(
        client, asset_id, risk_id, assignee_id=user.id
    )

    assert (
        client.get(f"/vulnerabilities/{vulnerability_id}").json()["assignee_id"]
        == user.id
    )


def test_create_vulnerability_with_nonexistent_assignee_is_404(client):
    asset_id = _create_asset(client)
    risk_id = _create_risk(client, asset_id)

    response = client.post("/vulnerabilities", json={
        "title": "t", "description": "d", "asset_id": asset_id,
        "risk_id": risk_id, "cvss_score": 5.0, "owner": "IT",
        "assignee_id": 999999
    })

    assert response.status_code == 404
    assert response.json() == {"detail": "Assignee not found"}


def test_create_vulnerability_with_cross_org_assignee_is_404(client, db_session):
    _make_org2(db_session)
    other_org_user = _make_user(db_session, email="other@example.com", org_id=ORG2)
    asset_id = _create_asset(client)
    risk_id = _create_risk(client, asset_id)

    response = client.post("/vulnerabilities", json={
        "title": "t", "description": "d", "asset_id": asset_id,
        "risk_id": risk_id, "cvss_score": 5.0, "owner": "IT",
        "assignee_id": other_org_user.id
    })

    assert response.status_code == 404
    assert response.json() == {"detail": "Assignee not found"}


def test_update_vulnerability_assignee_cross_org_is_404(client, db_session):
    _make_org2(db_session)
    other_org_user = _make_user(db_session, email="other2@example.com", org_id=ORG2)
    asset_id = _create_asset(client)
    risk_id = _create_risk(client, asset_id)
    vulnerability_id = _create_vulnerability(client, asset_id, risk_id)

    response = client.put(
        f"/vulnerabilities/{vulnerability_id}",
        json={"assignee_id": other_org_user.id}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Assignee not found"}


def test_create_risk_with_valid_assignee_succeeds(client, db_session):
    user = _make_user(db_session)
    asset_id = _create_asset(client)

    risk_id = _create_risk(client, asset_id, assignee_id=user.id)

    assert client.get(f"/risks/{risk_id}").json()["assignee_id"] == user.id


def test_assignee_id_filter_on_vulnerabilities(client, db_session):
    user = _make_user(db_session)
    asset_id = _create_asset(client)
    risk_id = _create_risk(client, asset_id)

    assigned_id = _create_vulnerability(
        client, asset_id, risk_id, assignee_id=user.id
    )
    _create_vulnerability(client, asset_id, risk_id)

    response = client.get(
        "/vulnerabilities", params={"assignee_id": user.id}
    )
    ids = [v["id"] for v in response.json()]
    assert ids == [assigned_id]


def test_backward_compat_owner_only_payload_still_works(client):
    """
    Existing clients that never send assignee_id/due_date must keep
    working exactly as before.
    """
    asset_id = _create_asset(client)
    risk_id = _create_risk(client, asset_id)

    response = client.post("/vulnerabilities", json={
        "title": "t", "description": "d", "asset_id": asset_id,
        "risk_id": risk_id, "cvss_score": 5.0, "owner": "IT"
    })

    assert response.status_code == 200
    assert response.json()["message"] == "Vulnerability created"


def test_assignee_rbac_denial(client, as_role):
    asset_id = _create_asset(client)
    risk_id = _create_risk(client, asset_id)
    vulnerability_id = _create_vulnerability(client, asset_id, risk_id)

    as_role(ROLE_AUDITOR)
    response = client.put(
        f"/vulnerabilities/{vulnerability_id}", json={"title": "new"}
    )
    assert response.status_code == 403


# --- evidence attachments --------------------------------------------------


def _seed_uploader(db):
    # The test client's default authenticated identity is
    # "test@example.com" (see conftest.py's override_get_current_user) -
    # a real matching User row is required since uploaded_by_id is a
    # NOT NULL FK, unlike audit_logs.actor which is free text.
    return _make_user(db, email="test@example.com", org_id=ORG1)


def test_upload_and_list_vulnerability_evidence(client, db_session):
    _seed_uploader(db_session)
    asset_id = _create_asset(client)
    risk_id = _create_risk(client, asset_id)
    vulnerability_id = _create_vulnerability(client, asset_id, risk_id)

    response = client.post(
        f"/vulnerabilities/{vulnerability_id}/evidence",
        files={"file": ("proof.txt", io.BytesIO(b"remediated"), "text/plain")}
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["file_name"] == "proof.txt"
    assert "stored_path" not in body

    listed = client.get(f"/vulnerabilities/{vulnerability_id}/evidence").json()
    assert len(listed) == 1
    assert listed[0]["id"] == body["id"]


def test_upload_evidence_bad_extension_is_400(client, db_session):
    _seed_uploader(db_session)
    asset_id = _create_asset(client)
    risk_id = _create_risk(client, asset_id)
    vulnerability_id = _create_vulnerability(client, asset_id, risk_id)

    response = client.post(
        f"/vulnerabilities/{vulnerability_id}/evidence",
        files={"file": ("payload.exe", io.BytesIO(b"x"), "application/octet-stream")}
    )
    assert response.status_code == 400


def test_download_evidence_returns_exact_bytes(client, db_session):
    _seed_uploader(db_session)
    asset_id = _create_asset(client)
    risk_id = _create_risk(client, asset_id)
    vulnerability_id = _create_vulnerability(client, asset_id, risk_id)

    content = b"exact evidence bytes"
    upload = client.post(
        f"/vulnerabilities/{vulnerability_id}/evidence",
        files={"file": ("proof.txt", io.BytesIO(content), "text/plain")}
    )
    attachment_id = upload.json()["id"]

    response = client.get(f"/evidence/{attachment_id}/download")
    assert response.status_code == 200
    assert response.content == content


def test_delete_evidence_removes_row_and_file(client, db_session):
    _seed_uploader(db_session)
    asset_id = _create_asset(client)
    risk_id = _create_risk(client, asset_id)
    vulnerability_id = _create_vulnerability(client, asset_id, risk_id)

    upload = client.post(
        f"/vulnerabilities/{vulnerability_id}/evidence",
        files={"file": ("proof.txt", io.BytesIO(b"data"), "text/plain")}
    )
    attachment_id = upload.json()["id"]

    import os
    from app.models.evidence_attachment import EvidenceAttachment
    stored_path = db_session.get(EvidenceAttachment, attachment_id).stored_path
    assert os.path.exists(stored_path)

    response = client.delete(f"/evidence/{attachment_id}")
    assert response.status_code == 200
    assert not os.path.exists(stored_path)

    assert client.get(f"/vulnerabilities/{vulnerability_id}/evidence").json() == []


def test_evidence_cross_org_download_is_404(client, db_session, as_user):
    _seed_uploader(db_session)
    _make_org2(db_session)
    asset_id = _create_asset(client)
    risk_id = _create_risk(client, asset_id)
    vulnerability_id = _create_vulnerability(client, asset_id, risk_id)

    upload = client.post(
        f"/vulnerabilities/{vulnerability_id}/evidence",
        files={"file": ("proof.txt", io.BytesIO(b"data"), "text/plain")}
    )
    attachment_id = upload.json()["id"]

    # A second org's caller must not be able to reach org 1's evidence.
    as_user(role=ROLE_ADMIN, org_id=ORG2)
    response = client.get(f"/evidence/{attachment_id}/download")
    assert response.status_code == 404

    delete_response = client.delete(f"/evidence/{attachment_id}")
    assert delete_response.status_code == 404


def test_risk_evidence_upload_and_list(client, db_session):
    _seed_uploader(db_session)
    asset_id = _create_asset(client)
    risk_id = _create_risk(client, asset_id)

    response = client.post(
        f"/risks/{risk_id}/evidence",
        files={"file": ("proof.txt", io.BytesIO(b"risk evidence"), "text/plain")}
    )
    assert response.status_code == 200, response.text

    listed = client.get(f"/risks/{risk_id}/evidence").json()
    assert len(listed) == 1
    assert listed[0]["risk_id"] == risk_id
