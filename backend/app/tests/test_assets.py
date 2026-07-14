"""
CyberRisk360

Purpose:
Tests for asset management endpoints.
"""

from app.models.vulnerability import Vulnerability


def test_create_asset(client):
    response = client.post("/assets", json={
        "name": "web-01", "asset_type": "server", "owner": "IT",
        "criticality": "High", "ip_address": "10.0.0.5", "environment": "prod"
    })

    assert response.status_code == 200
    assert response.json()["message"] == "Asset created"


def test_create_asset_missing_required_field(client):
    response = client.post("/assets", json={"name": "web-01"})

    assert response.status_code == 422


def test_create_asset_requires_admin_or_analyst(client, as_role):
    as_role("auditor")

    response = client.post("/assets", json={
        "name": "web-01", "asset_type": "server", "owner": "IT",
        "criticality": "High", "environment": "prod"
    })

    assert response.status_code == 403


def test_list_assets(client, seed_asset):
    response = client.get("/assets")

    assert response.status_code == 200
    assets = response.json()
    assert len(assets) == 1
    assert assets[0]["id"] == seed_asset


def test_asset_summary_not_found(client):
    response = client.get("/assets/999999/summary")

    assert response.status_code == 404
    assert response.json() == {"detail": "Asset not found"}


def test_asset_summary_counts_by_severity(client, seed_asset, db_session):
    db_session.add(Vulnerability(
        title="v1", description="d", asset_id=seed_asset,
        cvss_score=9.5, severity="Critical", status="Open", org_id=1
    ))
    db_session.add(Vulnerability(
        title="v2", description="d", asset_id=seed_asset,
        cvss_score=5.0, severity="Medium", status="Open", org_id=1
    ))
    db_session.commit()

    response = client.get(f"/assets/{seed_asset}/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["critical"] == 1
    assert body["medium"] == 1
    assert body["high"] == 0


def test_asset_vulnerabilities_empty(client, seed_asset):
    response = client.get(f"/assets/{seed_asset}/vulnerabilities")

    assert response.status_code == 200
    assert response.json() == []


def test_asset_vulnerabilities_seeded(client, seed_asset, db_session):
    db_session.add(Vulnerability(
        title="v1", description="d", asset_id=seed_asset,
        cvss_score=9.5, severity="Critical", status="Open", org_id=1, plugin_id="123"
    ))
    db_session.commit()

    response = client.get(f"/assets/{seed_asset}/vulnerabilities")

    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["plugin_id"] == "123"
    assert results[0]["severity"] == "Critical"


def test_asset_risk_summary(client, seed_asset, db_session):
    db_session.add(Vulnerability(
        title="v1", description="d", asset_id=seed_asset,
        cvss_score=9.5, severity="Critical", status="Open", org_id=1
    ))
    db_session.commit()

    response = client.get("/assets/risk-summary")

    assert response.status_code == 200
    assert len(response.json()) == 1
