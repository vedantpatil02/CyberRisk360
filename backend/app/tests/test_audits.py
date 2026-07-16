"""
CyberRisk360

Purpose:
Tests for the Audit Management API (audit engagements + findings) -
CRUD, close lifecycle, findings, RBAC (OVERSIGHT_ROLES write, READ_ROLES
read), and cross-org isolation.
"""

from app.models.organization import Organization
from app.core.constants import ROLE_ADMIN

ORG1 = 1
ORG2 = 2


def _create_audit(client, **overrides):
    payload = {"title": "Q3 SOC 2 Readiness Audit", "scope": "Access control"}
    payload.update(overrides)
    response = client.post("/audits", json=payload)
    assert response.status_code == 200
    return response.json()["id"]


def test_create_audit(client):
    response = client.post("/audits", json={
        "title": "Q3 SOC 2 Readiness Audit", "scope": "Access control"
    })

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Q3 SOC 2 Readiness Audit"
    assert body["status"] == "Planned"


def test_create_audit_requires_oversight_role(client, as_role):
    as_role("analyst")

    response = client.post("/audits", json={"title": "x"})

    assert response.status_code == 403


def test_create_audit_invalid_framework(client):
    response = client.post("/audits", json={"title": "x", "framework_id": 999999})

    assert response.status_code == 404


def test_list_audits(client):
    _create_audit(client)

    response = client.get("/audits")

    assert response.status_code == 200
    audits = response.json()
    assert len(audits) == 1


def test_list_audits_filter_by_status(client):
    _create_audit(client)

    response = client.get("/audits", params={"status": "Closed"})

    assert response.status_code == 200
    assert response.json() == []


def test_get_audit_by_id(client):
    audit_id = _create_audit(client)

    response = client.get(f"/audits/{audit_id}")

    assert response.status_code == 200
    assert response.json()["id"] == audit_id


def test_get_audit_not_found(client):
    response = client.get("/audits/999999")

    assert response.status_code == 404


def test_update_audit(client):
    audit_id = _create_audit(client)

    response = client.put(f"/audits/{audit_id}", json={"status": "In Progress"})

    assert response.status_code == 200
    assert response.json()["status"] == "In Progress"


def test_update_audit_requires_oversight_role(client, as_role):
    audit_id = _create_audit(client)
    as_role("analyst")

    response = client.put(f"/audits/{audit_id}", json={"status": "In Progress"})

    assert response.status_code == 403


def test_close_audit(client):
    audit_id = _create_audit(client)

    response = client.patch(f"/audits/{audit_id}/close")

    assert response.status_code == 200
    assert response.json()["status"] == "Closed"


def test_close_audit_already_closed(client):
    audit_id = _create_audit(client)
    client.patch(f"/audits/{audit_id}/close")

    response = client.patch(f"/audits/{audit_id}/close")

    assert response.status_code == 400


def test_close_audit_not_found(client):
    response = client.patch("/audits/999999/close")

    assert response.status_code == 404


def test_create_finding(client):
    audit_id = _create_audit(client)

    response = client.post(f"/audits/{audit_id}/findings", json={
        "title": "MFA not enforced", "severity": "High"
    })

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "MFA not enforced"
    assert body["severity"] == "High"
    assert body["status"] == "Open"


def test_create_finding_audit_not_found(client):
    response = client.post("/audits/999999/findings", json={"title": "x"})

    assert response.status_code == 404


def test_create_finding_requires_oversight_role(client, as_role):
    audit_id = _create_audit(client)
    as_role("analyst")

    response = client.post(f"/audits/{audit_id}/findings", json={"title": "x"})

    assert response.status_code == 403


def test_list_findings(client):
    audit_id = _create_audit(client)
    client.post(f"/audits/{audit_id}/findings", json={"title": "Finding 1"})
    client.post(f"/audits/{audit_id}/findings", json={"title": "Finding 2"})

    response = client.get(f"/audits/{audit_id}/findings")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_update_finding_status(client):
    audit_id = _create_audit(client)
    finding_response = client.post(f"/audits/{audit_id}/findings", json={"title": "x"})
    finding_id = finding_response.json()["id"]

    response = client.put(f"/findings/{finding_id}", json={"status": "Remediated"})

    assert response.status_code == 200
    assert response.json()["status"] == "Remediated"


def test_update_finding_not_found(client):
    response = client.put("/findings/999999", json={"status": "Remediated"})

    assert response.status_code == 404


# --- cross-org isolation -----------------------------------------------

def _make_org2(db):
    db.add(Organization(id=ORG2, name="Second Org", slug="second"))
    db.commit()


def test_audits_are_isolated_by_org(client, db_session, as_user):
    _make_org2(db_session)

    as_user(role=ROLE_ADMIN, org_id=ORG1)
    client.post("/audits", json={"title": "Org1 Audit"})

    as_user(role=ROLE_ADMIN, org_id=ORG2)
    org2_audits = client.get("/audits").json()

    assert org2_audits == []


def test_cross_org_audit_detail_is_404(client, db_session, as_user):
    _make_org2(db_session)

    as_user(role=ROLE_ADMIN, org_id=ORG1)
    audit_id = _create_audit(client)

    as_user(role=ROLE_ADMIN, org_id=ORG2)
    response = client.get(f"/audits/{audit_id}")

    assert response.status_code == 404
