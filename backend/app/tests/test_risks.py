"""
CyberRisk360

Purpose:
Tests for risk management endpoints.
"""


def _create_asset(client):
    response = client.post("/assets", json={
        "name": "web-01", "asset_type": "server", "owner": "IT",
        "criticality": "High", "environment": "prod"
    })
    assert response.status_code == 200
    return client.get("/assets").json()[0]["id"]


def test_list_risks_empty(client):
    response = client.get("/risks")

    assert response.status_code == 200
    assert response.json() == []


def test_list_risks_with_data(client):
    asset_id = _create_asset(client)

    client.post("/risks", json={
        "title": "Risk 1", "description": "d", "asset_id": asset_id,
        "impact": 4, "likelihood": 3, "owner": "IT"
    })

    response = client.get("/risks")

    assert response.status_code == 200
    risks = response.json()
    assert len(risks) == 1
    assert risks[0]["title"] == "Risk 1"
    assert risks[0]["risk_score"] == 12


def test_new_risk_has_remediation_fields_null_by_default(client):
    asset_id = _create_asset(client)

    client.post("/risks", json={
        "title": "Risk 1", "description": "d", "asset_id": asset_id,
        "impact": 4, "likelihood": 3, "owner": "IT"
    })

    risk = client.get("/risks").json()[0]
    assert risk["assignee_id"] is None
    assert risk["created_at"] is not None
    # due_date is auto-computed from risk_level, not null.
    assert risk["due_date"] is not None
