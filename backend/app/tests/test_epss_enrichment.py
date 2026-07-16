"""
CyberRisk360

Purpose:
Tests for EPSS integration - the per-CVE cache/refresh
(app/services/enrichment/epss_enrichment.py) and the
GET /vulnerabilities/{id}/epss-score endpoint. Mirrors
test_cisa_kev.py's unittest.mock.patch style - every test patches
app.services.enrichment.epss_enrichment.requests.get directly so no
real network call is ever made.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import requests

from app.models.epss_score_cache import EpssScoreCache
from app.repositories.vulnerabilities.vulnerability_repository import (
    create_vulnerability,
)
from app.services.enrichment.epss_enrichment import get_epss_score


def _epss_payload(**overrides):
    entry = {
        "cve": "CVE-2021-44228",
        "epss": "0.999990000",
        "percentile": "1.000000000",
        "date": "2026-07-15",
    }
    entry.update(overrides)
    return {
        "status": "OK",
        "status-code": 200,
        "total": 1,
        "data": [entry],
    }


def _empty_payload():
    return {"status": "OK", "status-code": 200, "total": 0, "data": []}


def _create_asset(client):
    response = client.post("/assets", json={
        "name": "web-01", "asset_type": "server", "owner": "IT",
        "criticality": "High", "environment": "prod"
    })
    assert response.status_code == 200
    return client.get("/assets").json()[0]["id"]


def _create_vulnerability_with_cve(db, client, cve_id):
    asset_id = _create_asset(client)

    vulnerability = create_vulnerability(
        db,
        title="Log4Shell", description="d", cvss_score=10.0,
        severity="Critical", status="Open", asset_id=asset_id,
        cve_id=cve_id, org_id=1,
    )
    db.commit()

    return vulnerability.id


# --- service: cache-hit / cache-miss shape ---------------------------------


def test_no_cve_id_short_circuits_without_network_call(db_session):
    with patch("app.services.enrichment.epss_enrichment.requests.get") as mock_get:
        result = get_epss_score(db_session, None)

    mock_get.assert_not_called()
    assert result is None


def test_fresh_cache_skips_refetch(db_session):
    db_session.add(EpssScoreCache(
        cve_id="CVE-2021-44228",
        epss_score=0.99999,
        percentile=1.0,
        score_date="2026-07-15",
        status="ok",
        fetched_at=datetime.now(timezone.utc),
    ))
    db_session.commit()

    with patch("app.services.enrichment.epss_enrichment.requests.get") as mock_get:
        result = get_epss_score(db_session, "CVE-2021-44228")

    mock_get.assert_not_called()
    assert result["epss_score"] == 0.99999
    assert result["percentile"] == 1.0


def test_stale_cache_triggers_refetch(db_session):
    db_session.add(EpssScoreCache(
        cve_id="CVE-2021-44228",
        epss_score=0.5,
        percentile=0.5,
        score_date="2026-07-01",
        status="ok",
        fetched_at=datetime.now(timezone.utc) - timedelta(hours=48),
    ))
    db_session.commit()

    fake_response = Mock(status_code=200, json=lambda: _epss_payload())

    with patch(
        "app.services.enrichment.epss_enrichment.requests.get",
        return_value=fake_response,
    ) as mock_get:
        result = get_epss_score(db_session, "CVE-2021-44228")

    mock_get.assert_called_once()
    # The stale value was replaced with the freshly-fetched one.
    assert result["epss_score"] == 0.99999


def test_empty_cache_triggers_fetch_and_cve_not_found(db_session):
    fake_response = Mock(status_code=200, json=lambda: _empty_payload())

    with patch(
        "app.services.enrichment.epss_enrichment.requests.get",
        return_value=fake_response,
    ):
        result = get_epss_score(db_session, "CVE-9999-99999")

    assert result is None


def test_retry_then_succeed(db_session):
    failure = Mock(status_code=500)
    success = Mock(status_code=200, json=lambda: _epss_payload())

    with patch(
        "app.services.enrichment.epss_enrichment.requests.get",
        side_effect=[failure, success],
    ) as mock_get, patch("app.services.enrichment.epss_enrichment.time.sleep"):
        result = get_epss_score(db_session, "CVE-2021-44228")

    assert mock_get.call_count == 2
    assert result["epss_score"] == 0.99999


def test_network_failure_falls_back_to_cached_failure(db_session):
    db_session.add(EpssScoreCache(
        cve_id="CVE-2021-44228",
        status="failed",
        fetched_at=datetime.now(timezone.utc),
    ))
    db_session.commit()

    with patch(
        "app.services.enrichment.epss_enrichment.requests.get",
        side_effect=requests.ConnectionError("network down"),
    ) as mock_get, patch("app.services.enrichment.epss_enrichment.time.sleep"):
        result = get_epss_score(db_session, "CVE-2021-44228")

    # Cached failure is still within its retry backoff - no network
    # call is even attempted.
    mock_get.assert_not_called()
    assert result is None


# --- API ---------------------------------------------------------------


def test_epss_score_endpoint(client, db_session):
    vulnerability_id = _create_vulnerability_with_cve(
        db_session, client, "CVE-2021-44228"
    )

    fake_response = Mock(status_code=200, json=lambda: _epss_payload())

    with patch(
        "app.services.enrichment.epss_enrichment.requests.get",
        return_value=fake_response,
    ):
        response = client.get(f"/vulnerabilities/{vulnerability_id}/epss-score")

    assert response.status_code == 200
    assert response.json()["epss_score"] == 0.99999


def test_epss_score_endpoint_no_cve_id(client, db_session):
    asset_id = _create_asset(client)
    vulnerability = create_vulnerability(
        db_session,
        title="No CVE", description="d", cvss_score=5.0,
        severity="Medium", status="Open", asset_id=asset_id,
        cve_id=None, org_id=1,
    )
    db_session.commit()

    with patch("app.services.enrichment.epss_enrichment.requests.get") as mock_get:
        response = client.get(f"/vulnerabilities/{vulnerability.id}/epss-score")

    mock_get.assert_not_called()
    assert response.status_code == 200
    assert response.json() == {"epss_score": None, "percentile": None, "date": None}


def test_epss_score_endpoint_not_found(client):
    response = client.get("/vulnerabilities/999999/epss-score")

    assert response.status_code == 404


def test_epss_score_endpoint_requires_read_role(client, db_session, as_role):
    vulnerability_id = _create_vulnerability_with_cve(
        db_session, client, "CVE-2021-44228"
    )

    as_role("pentester")

    response = client.get(f"/vulnerabilities/{vulnerability_id}/epss-score")

    assert response.status_code == 403
