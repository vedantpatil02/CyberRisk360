"""
CyberRisk360

Purpose:
Tests for CISA KEV integration - the whole-catalog cache/refresh
(app/services/enrichment/cisa_kev.py) and the
GET /vulnerabilities/{id}/kev-status endpoint. Mirrors
test_cve_enrichment.py's unittest.mock.patch style - every test
patches app.services.enrichment.cisa_kev.requests.get directly so no
real network call is ever made.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import requests

from app.models.cisa_kev_entry import CisaKevEntry
from app.repositories.vulnerabilities.vulnerability_repository import (
    create_vulnerability,
)
from app.services.enrichment.cisa_kev import check_kev_status


def _kev_payload(**overrides):
    entry = {
        "cveID": "CVE-2021-44228",
        "vulnerabilityName": "Apache Log4j2 RCE",
        "dateAdded": "2021-12-10",
        "dueDate": "2021-12-24",
        "requiredAction": "Apply mitigations per vendor instructions.",
        "knownRansomwareCampaignUse": "Known",
        "notes": "https://nvd.nist.gov/vuln/detail/CVE-2021-44228",
    }
    entry.update(overrides)
    return {
        "title": "CISA KEV Catalog",
        "catalogVersion": "test",
        "dateReleased": "2026-01-01T00:00:00Z",
        "count": 1,
        "vulnerabilities": [entry],
    }


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
    with patch("app.services.enrichment.cisa_kev.requests.get") as mock_get:
        result = check_kev_status(db_session, None)

    mock_get.assert_not_called()
    assert result == {"in_kev": False}


def test_fresh_cache_skips_refetch(db_session):
    db_session.add(CisaKevEntry(
        cve_id="CVE-2021-44228",
        vulnerability_name="Apache Log4j2 RCE",
        known_ransomware_use="Known",
        fetched_at=datetime.now(timezone.utc),
    ))
    db_session.commit()

    with patch("app.services.enrichment.cisa_kev.requests.get") as mock_get:
        result = check_kev_status(db_session, "CVE-2021-44228")

    mock_get.assert_not_called()
    assert result["in_kev"] is True
    assert result["known_ransomware_use"] == "Known"


def test_stale_cache_triggers_refetch(db_session):
    db_session.add(CisaKevEntry(
        cve_id="CVE-OLD-0001",
        fetched_at=datetime.now(timezone.utc) - timedelta(hours=48),
    ))
    db_session.commit()

    fake_response = Mock(status_code=200, json=lambda: _kev_payload())

    with patch(
        "app.services.enrichment.cisa_kev.requests.get",
        return_value=fake_response,
    ) as mock_get:
        result = check_kev_status(db_session, "CVE-2021-44228")

    mock_get.assert_called_once()
    assert result["in_kev"] is True
    assert result["vulnerability_name"] == "Apache Log4j2 RCE"
    # The stale entry was replaced, not left alongside the new catalog.
    assert db_session.query(CisaKevEntry).filter(
        CisaKevEntry.cve_id == "CVE-OLD-0001"
    ).first() is None


def test_empty_cache_triggers_fetch_and_cve_not_in_catalog(db_session):
    fake_response = Mock(status_code=200, json=lambda: _kev_payload())

    with patch(
        "app.services.enrichment.cisa_kev.requests.get",
        return_value=fake_response,
    ):
        result = check_kev_status(db_session, "CVE-9999-99999")

    assert result == {"in_kev": False}


def test_retry_then_succeed(db_session):
    failure = Mock(status_code=500)
    success = Mock(status_code=200, json=lambda: _kev_payload())

    with patch(
        "app.services.enrichment.cisa_kev.requests.get",
        side_effect=[failure, success],
    ) as mock_get, patch("app.services.enrichment.cisa_kev.time.sleep"):
        result = check_kev_status(db_session, "CVE-2021-44228")

    assert mock_get.call_count == 2
    assert result["in_kev"] is True


def test_network_failure_falls_back_to_existing_cache(db_session):
    db_session.add(CisaKevEntry(
        cve_id="CVE-2021-44228",
        vulnerability_name="Apache Log4j2 RCE",
        fetched_at=datetime.now(timezone.utc) - timedelta(hours=48),
    ))
    db_session.commit()

    with patch(
        "app.services.enrichment.cisa_kev.requests.get",
        side_effect=requests.ConnectionError("network down"),
    ), patch("app.services.enrichment.cisa_kev.time.sleep"):
        result = check_kev_status(db_session, "CVE-2021-44228")

    # Refresh failed, but the (stale) existing cache still answers.
    assert result["in_kev"] is True


# --- API ---------------------------------------------------------------


def test_kev_status_endpoint(client, db_session):
    vulnerability_id = _create_vulnerability_with_cve(
        db_session, client, "CVE-2021-44228"
    )

    fake_response = Mock(status_code=200, json=lambda: _kev_payload())

    with patch(
        "app.services.enrichment.cisa_kev.requests.get",
        return_value=fake_response,
    ):
        response = client.get(f"/vulnerabilities/{vulnerability_id}/kev-status")

    assert response.status_code == 200
    assert response.json()["in_kev"] is True


def test_kev_status_endpoint_not_found(client):
    response = client.get("/vulnerabilities/999999/kev-status")

    assert response.status_code == 404


def test_kev_status_endpoint_requires_read_role(client, db_session, as_role):
    vulnerability_id = _create_vulnerability_with_cve(
        db_session, client, "CVE-2021-44228"
    )

    as_role("pentester")

    response = client.get(f"/vulnerabilities/{vulnerability_id}/kev-status")

    assert response.status_code == 403
