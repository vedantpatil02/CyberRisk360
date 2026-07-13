"""
CyberRisk360

Purpose:
Tests for dashboard aggregation endpoints.
"""

from app.models.vulnerability import Vulnerability
from app.tests.test_mapping_engine import _import_nist_csf


def test_overview_empty(client):
    response = client.get("/dashboard/overview")

    assert response.status_code == 200
    body = response.json()
    assert body["total_assets"] == 0
    assert body["total_vulnerabilities"] == 0
    assert body["top_assets"] == []


def test_overview_with_data(client, seed_asset, db_session):
    db_session.add(Vulnerability(
        title="v1", description="d", asset_id=seed_asset,
        cvss_score=9.5, severity="Critical", status="Open"
    ))
    db_session.commit()

    response = client.get("/dashboard/overview")

    assert response.status_code == 200
    body = response.json()
    assert body["total_assets"] == 1
    assert body["total_vulnerabilities"] == 1
    assert body["critical"] == 1
    assert body["open"] == 1
    assert len(body["top_assets"]) == 1
    assert body["top_assets"][0]["asset_id"] == seed_asset


def test_grc_dashboard(client, db_session):
    _import_nist_csf(db_session)

    response = client.get("/dashboard/grc/nist-csf")

    assert response.status_code == 200
    body = response.json()
    assert body["framework"] == "nist-csf"
    assert body["total_controls"] > 0


def test_executive_dashboard(client, seed_asset, db_session):
    _import_nist_csf(db_session)

    db_session.add(Vulnerability(
        title="v1", description="d", asset_id=seed_asset,
        cvss_score=9.5, severity="Critical", status="Open"
    ))
    db_session.commit()

    response = client.get("/dashboard/executive")

    assert response.status_code == 200
    body = response.json()
    assert body["assets"]["total"] == 1
    assert body["vulnerabilities"]["total"] == 1
    assert body["vulnerabilities"]["critical"] == 1
    assert body["controls"]["total"] > 0
