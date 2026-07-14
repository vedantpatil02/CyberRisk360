"""
CyberRisk360

Tests for filtering, sorting, and pagination on the list endpoints.
Covers vulnerabilities in depth (the high-volume endpoint) plus the
shared behavior on assets/risks.
"""

from app.repositories.assets.asset_repository import create_asset
from app.repositories.vulnerabilities.vulnerability_repository import (
    create_vulnerability,
)


def _asset(db, ip="10.0.0.1", criticality="High"):
    return create_asset(
        db,
        name=f"Host-{ip}",
        asset_type="server",
        owner="Team",
        criticality=criticality,
        ip_address=ip,
        environment="prod",
    )


def _vuln(db, asset_id, title, severity, cvss, status="Open"):
    create_vulnerability(
        db,
        title=title,
        plugin_id=None,
        cve_id=None,
        solution=None,
        ip_address="10.0.0.1",
        description="d",
        asset_id=asset_id,
        cvss_score=cvss,
        severity=severity,
        owner="Imported",
        status=status,
    )
    db.commit()


def _seed(db):
    asset = _asset(db)
    _vuln(db, asset.id, "Critical bug", "Critical", 9.8)
    _vuln(db, asset.id, "High bug", "High", 7.5)
    _vuln(db, asset.id, "Medium bug", "Medium", 5.0, status="Closed")
    _vuln(db, asset.id, "Low bug", "Low", 2.0)
    return asset


def test_no_params_returns_all(client, db_session):
    _seed(db_session)

    vulns = client.get("/vulnerabilities").json()

    assert len(vulns) == 4


def test_filter_by_severity(client, db_session):
    _seed(db_session)

    vulns = client.get("/vulnerabilities?severity=critical").json()

    assert len(vulns) == 1
    assert vulns[0]["severity"] == "Critical"


def test_filter_by_status(client, db_session):
    _seed(db_session)

    vulns = client.get("/vulnerabilities?status=closed").json()

    assert len(vulns) == 1
    assert vulns[0]["status"] == "Closed"


def test_sort_by_cvss_desc(client, db_session):
    _seed(db_session)

    vulns = client.get("/vulnerabilities?sort_by=cvss_score&order=desc").json()

    scores = [v["cvss_score"] for v in vulns]
    assert scores == sorted(scores, reverse=True)
    assert scores[0] == 9.8


def test_limit_and_offset(client, db_session):
    _seed(db_session)

    page1 = client.get(
        "/vulnerabilities?sort_by=cvss_score&order=desc&limit=2&offset=0"
    ).json()
    page2 = client.get(
        "/vulnerabilities?sort_by=cvss_score&order=desc&limit=2&offset=2"
    ).json()

    assert len(page1) == 2
    assert len(page2) == 2
    # No overlap between pages.
    ids = {v["id"] for v in page1} | {v["id"] for v in page2}
    assert len(ids) == 4


def test_invalid_order_rejected(client, db_session):
    _seed(db_session)

    response = client.get("/vulnerabilities?order=sideways")

    assert response.status_code == 422


def test_limit_over_max_rejected(client, db_session):
    _seed(db_session)

    response = client.get("/vulnerabilities?limit=99999")

    assert response.status_code == 422


def test_assets_filter_and_paginate(client, db_session):
    _asset(db_session, ip="10.0.0.1", criticality="High")
    _asset(db_session, ip="10.0.0.2", criticality="Low")

    high = client.get("/assets?criticality=high").json()
    assert len(high) == 1
    assert high[0]["criticality"] == "High"

    limited = client.get("/assets?limit=1").json()
    assert len(limited) == 1


def test_risks_filter_by_source(client, db_session):
    asset = _asset(db_session)
    _vuln(db_session, asset.id, "Critical bug", "Critical", 9.8)
    # Auto-generate a risk for the asset.
    assert client.post("/risks/generate").status_code == 200

    auto = client.get("/risks?source=auto").json()
    assert auto
    assert all(r["source"] == "auto" for r in auto)
