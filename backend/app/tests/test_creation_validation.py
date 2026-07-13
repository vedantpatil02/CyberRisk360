"""
CyberRisk360

Purpose:
Regression tests for foreign-key and value validation on the
create endpoints for controls, risks, and vulnerabilities.

Found via a full endpoint walkthrough: none of these endpoints
checked that a referenced id (category_id / asset_id / risk_id)
actually existed before persisting, and vulnerability creation
validated cvss_score on update but not on create. Unvalidated
FK references aren't just bad data - a control with a dangling
category_id crashes GET /controls/{id}/vulnerabilities with an
unhandled AttributeError ('NoneType' object has no attribute
'framework') because downstream code assumes control.category
is never None.
"""


def _create_asset(client):
    response = client.post("/assets", json={
        "name": "web-01",
        "asset_type": "server",
        "owner": "IT",
        "criticality": "High",
        "ip_address": "10.0.0.5",
        "environment": "prod"
    })
    assert response.status_code == 200
    return client.get("/assets").json()[0]["id"]


def _create_risk(client, asset_id):
    response = client.post("/risks", json={
        "title": "Risk 1", "description": "d", "asset_id": asset_id,
        "impact": 3, "likelihood": 3, "owner": "IT"
    })
    assert response.status_code == 200
    return 1  # first risk created in this test's fresh db


# --- controls ------------------------------------------------------------


def test_create_control_rejects_unknown_category_id(client):
    response = client.post("/controls", json={
        "control_id": "X-1", "title": "t", "description": "d",
        "category_id": 999999
    })

    assert response.status_code == 404
    assert response.json() == {"detail": "Category not found"}
    assert client.get("/controls").json() == []


def test_create_control_with_bad_category_never_reaches_crash_path(client):
    """
    Defense in depth: even if a bad category_id somehow got past
    creation, listing controls/vulnerabilities must not 500. Proven
    here by confirming rejection means no orphaned control is ever
    stored to trip that code path.
    """
    client.post("/controls", json={
        "control_id": "X-1", "title": "t", "description": "d",
        "category_id": 999999
    })

    response = client.get("/controls/1/vulnerabilities")
    # No control with id 1 was ever created, so this is a normal
    # "not found" - not a 500 from a dangling category reference.
    assert response.status_code == 404
    assert response.json() == {"detail": "Control not found"}


# --- risks -----------------------------------------------------------------


def test_create_risk_rejects_unknown_asset_id(client):
    response = client.post("/risks", json={
        "title": "t", "description": "d", "asset_id": 999999,
        "impact": 3, "likelihood": 3, "owner": "IT"
    })

    assert response.status_code == 404
    assert response.json() == {"detail": "Asset not found"}
    assert client.get("/risks/1").status_code == 404
    assert client.get("/risks/1").json() == {"detail": "Risk not found"}


def test_create_risk_with_valid_asset_succeeds(client):
    asset_id = _create_asset(client)

    response = client.post("/risks", json={
        "title": "t", "description": "d", "asset_id": asset_id,
        "impact": 3, "likelihood": 3, "owner": "IT"
    })

    assert response.status_code == 200
    assert response.json()["message"] == "Risk created"


# --- vulnerabilities ---------------------------------------------------------


def test_create_vulnerability_rejects_unknown_asset_id(client):
    response = client.post("/vulnerabilities", json={
        "title": "t", "description": "d", "asset_id": 999999,
        "risk_id": 999999, "cvss_score": 5.0, "owner": "IT"
    })

    assert response.status_code == 404
    assert response.json() == {"detail": "Asset not found"}
    assert client.get("/vulnerabilities").json() == []


def test_create_vulnerability_rejects_unknown_risk_id(client):
    asset_id = _create_asset(client)

    response = client.post("/vulnerabilities", json={
        "title": "t", "description": "d", "asset_id": asset_id,
        "risk_id": 999999, "cvss_score": 5.0, "owner": "IT"
    })

    assert response.status_code == 404
    assert response.json() == {"detail": "Risk not found"}
    assert client.get("/vulnerabilities").json() == []


def test_create_vulnerability_rejects_out_of_range_cvss_score(client):
    asset_id = _create_asset(client)
    risk_id = _create_risk(client, asset_id)

    response = client.post("/vulnerabilities", json={
        "title": "t", "description": "d", "asset_id": asset_id,
        "risk_id": risk_id, "cvss_score": 15.0, "owner": "IT"
    })

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid CVSS score"}
    assert client.get("/vulnerabilities").json() == []


def test_create_vulnerability_with_valid_refs_succeeds(client):
    asset_id = _create_asset(client)
    risk_id = _create_risk(client, asset_id)

    response = client.post("/vulnerabilities", json={
        "title": "t", "description": "d", "asset_id": asset_id,
        "risk_id": risk_id, "cvss_score": 8.5, "owner": "IT"
    })

    assert response.status_code == 200
    assert response.json()["message"] == "Vulnerability created"
    assert len(client.get("/vulnerabilities").json()) == 1
