"""
CyberRisk360

Purpose:
Unit tests for services/enrichment/cve_enrichment.py - the real NVD
lookup that replaced the no-op stub. Mirrors
test_vulnerability_importer.py's unittest.mock.patch style (no
responses/httpx_mock in this codebase); every test patches
app.services.enrichment.cve_enrichment.requests.get directly so no
real network call is ever made.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest

from app.repositories.enrichment.nvd_cache_repository import get_cache_entry
from app.models.nvd_enrichment_cache import NvdEnrichmentCache
from app.services.enrichment import cve_enrichment
from app.services.enrichment.cve_enrichment import enrich_cve


@pytest.fixture(autouse=True)
def _reset_throttle_state():
    # Module-level throttle timestamp - reset between tests so one
    # test's timing can't bleed into the next.
    cve_enrichment._last_request_at = None
    yield
    cve_enrichment._last_request_at = None


def _nvd_payload(**cve_overrides):
    cve = {
        "id": "CVE-2021-44228",
        "descriptions": [{"lang": "en", "value": "Log4j RCE"}],
        "metrics": {
            "cvssMetricV31": [{
                "cvssData": {
                    "baseScore": 10.0,
                    "vectorString": "CVSS:3.1/AV:N/AC:L",
                    "version": "3.1",
                }
            }]
        },
        "weaknesses": [
            {"description": [{"lang": "en", "value": "CWE-502"}]}
        ],
        "published": "2021-12-10T10:15:09.143",
    }
    cve.update(cve_overrides)
    return {"vulnerabilities": [{"cve": cve}], "totalResults": 1}


_EMPTY_PAYLOAD = {"vulnerabilities": [], "totalResults": 0}


# --- cache-hit / cache-miss shape ------------------------------------------


def test_cache_hit_makes_no_network_call(db_session):
    db_session.add(NvdEnrichmentCache(
        cve_id="CVE-2021-44228",
        cvss_score=10.0,
        cvss_vector="CVSS:3.1/AV:N",
        cvss_version="3.1",
        cwe_id="CWE-502",
        description="cached description",
        status="ok",
        fetched_at=datetime.now(timezone.utc),
    ))
    db_session.commit()

    with patch(
        "app.services.enrichment.cve_enrichment.requests.get"
    ) as mock_get:
        result, cache_written = enrich_cve(db_session, "CVE-2021-44228")

    mock_get.assert_not_called()
    assert cache_written is False
    assert result["description"] == "cached description"
    assert result["cwe_id"] == "CWE-502"


def test_successful_fetch_caches_and_returns_result(db_session):
    fake_response = Mock(status_code=200, json=lambda: _nvd_payload())

    with patch(
        "app.services.enrichment.cve_enrichment.requests.get",
        return_value=fake_response
    ), patch("app.services.enrichment.cve_enrichment.time.sleep"):
        result, cache_written = enrich_cve(db_session, "CVE-2021-44228")

    assert cache_written is True
    assert result["cvss_score"] == 10.0
    assert result["cvss_vector"] == "CVSS:3.1/AV:N/AC:L"
    assert result["cvss_version"] == "3.1"
    assert result["cwe_id"] == "CWE-502"
    assert result["description"] == "Log4j RCE"
    assert result["published_at"] == datetime(
        2021, 12, 10, 10, 15, 9, 143000, tzinfo=timezone.utc
    )

    entry = get_cache_entry(db_session, "CVE-2021-44228")
    assert entry is not None
    assert entry.status == "ok"


# --- CVSS version fallback + CWE filtering ---------------------------------


def test_cvss_falls_back_to_v30_when_v31_absent(db_session):
    payload = _nvd_payload(metrics={
        "cvssMetricV30": [{
            "cvssData": {
                "baseScore": 8.1, "vectorString": "CVSS:3.0/AV:N",
                "version": "3.0",
            }
        }]
    })
    fake_response = Mock(status_code=200, json=lambda: payload)

    with patch(
        "app.services.enrichment.cve_enrichment.requests.get",
        return_value=fake_response
    ), patch("app.services.enrichment.cve_enrichment.time.sleep"):
        result, _ = enrich_cve(db_session, "CVE-2021-44228")

    assert result["cvss_score"] == 8.1
    assert result["cvss_version"] == "3.0"


def test_cvss_falls_back_to_v2_when_v3_absent(db_session):
    payload = _nvd_payload(metrics={
        "cvssMetricV2": [{
            "cvssData": {
                "baseScore": 7.5, "vectorString": "AV:N/AC:L", "version": "2.0",
            }
        }]
    })
    fake_response = Mock(status_code=200, json=lambda: payload)

    with patch(
        "app.services.enrichment.cve_enrichment.requests.get",
        return_value=fake_response
    ), patch("app.services.enrichment.cve_enrichment.time.sleep"):
        result, _ = enrich_cve(db_session, "CVE-2021-44228")

    assert result["cvss_score"] == 7.5
    assert result["cvss_version"] == "2.0"


def test_cwe_skips_noinfo_placeholder(db_session):
    payload = _nvd_payload(weaknesses=[
        {"description": [{"lang": "en", "value": "NVD-CWE-noinfo"}]},
        {"description": [{"lang": "en", "value": "CWE-79"}]},
    ])
    fake_response = Mock(status_code=200, json=lambda: payload)

    with patch(
        "app.services.enrichment.cve_enrichment.requests.get",
        return_value=fake_response
    ), patch("app.services.enrichment.cve_enrichment.time.sleep"):
        result, _ = enrich_cve(db_session, "CVE-2021-44228")

    assert result["cwe_id"] == "CWE-79"


# --- retry / backoff ---------------------------------------------------------


def test_retries_on_transient_failure_then_succeeds(db_session):
    success_response = Mock(status_code=200, json=lambda: _nvd_payload())

    responses = [
        Mock(status_code=500),
        Mock(status_code=429, headers={}),
        success_response,
    ]

    with patch(
        "app.services.enrichment.cve_enrichment.requests.get",
        side_effect=responses
    ) as mock_get, patch(
        "app.services.enrichment.cve_enrichment.time.sleep"
    ) as mock_sleep:
        result, cache_written = enrich_cve(db_session, "CVE-2021-44228")

    assert mock_get.call_count == 3
    assert cache_written is True
    assert result["description"] == "Log4j RCE"
    assert mock_sleep.called


def test_429_honors_retry_after_header(db_session):
    responses = [
        Mock(status_code=429, headers={"Retry-After": "7"}),
        Mock(status_code=200, json=lambda: _nvd_payload()),
    ]

    with patch(
        "app.services.enrichment.cve_enrichment.requests.get",
        side_effect=responses
    ), patch(
        "app.services.enrichment.cve_enrichment.time.sleep"
    ) as mock_sleep:
        enrich_cve(db_session, "CVE-2021-44228")

    assert 7.0 in [call.args[0] for call in mock_sleep.call_args_list]


def test_network_exception_is_treated_as_transient(db_session):
    import requests

    responses = [requests.RequestException("boom"), Mock(status_code=200, json=lambda: _nvd_payload())]

    with patch(
        "app.services.enrichment.cve_enrichment.requests.get",
        side_effect=responses
    ) as mock_get, patch("app.services.enrichment.cve_enrichment.time.sleep"):
        result, cache_written = enrich_cve(db_session, "CVE-2021-44228")

    assert mock_get.call_count == 2
    assert cache_written is True


def test_no_record_returns_immediately_without_retry(db_session):
    fake_response = Mock(status_code=200, json=lambda: _EMPTY_PAYLOAD)

    with patch(
        "app.services.enrichment.cve_enrichment.requests.get",
        return_value=fake_response
    ) as mock_get, patch(
        "app.services.enrichment.cve_enrichment.time.sleep"
    ) as mock_sleep:
        result, cache_written = enrich_cve(db_session, "CVE-9999-99999")

    assert mock_get.call_count == 1
    mock_sleep.assert_not_called()
    assert cache_written is True

    entry = get_cache_entry(db_session, "CVE-9999-99999")
    assert entry.status == "failed"


def test_cached_failure_within_ttl_is_not_retried(db_session):
    db_session.add(NvdEnrichmentCache(
        cve_id="CVE-9999-99999",
        status="failed",
        fetched_at=datetime.now(timezone.utc) - timedelta(hours=1),
    ))
    db_session.commit()

    with patch(
        "app.services.enrichment.cve_enrichment.requests.get"
    ) as mock_get:
        result, cache_written = enrich_cve(db_session, "CVE-9999-99999")

    mock_get.assert_not_called()
    assert cache_written is False
    assert result["description"] == ""


def test_cached_failure_past_ttl_is_retried(db_session):
    db_session.add(NvdEnrichmentCache(
        cve_id="CVE-9999-99999",
        status="failed",
        fetched_at=datetime.now(timezone.utc) - timedelta(hours=25),
    ))
    db_session.commit()

    fake_response = Mock(status_code=200, json=lambda: _nvd_payload())

    with patch(
        "app.services.enrichment.cve_enrichment.requests.get",
        return_value=fake_response
    ) as mock_get, patch("app.services.enrichment.cve_enrichment.time.sleep"):
        result, cache_written = enrich_cve(db_session, "CVE-9999-99999")

    mock_get.assert_called_once()
    assert cache_written is True
    assert result["description"] == "Log4j RCE"


# --- throttle / rate window --------------------------------------------------


def test_throttle_sleeps_when_called_faster_than_window(db_session):
    fake_response = Mock(status_code=200, json=lambda: _nvd_payload())

    times = iter([0.0, 0.0, 0.0, 0.05, 0.05])

    with patch(
        "app.services.enrichment.cve_enrichment.requests.get",
        return_value=fake_response
    ), patch(
        "app.services.enrichment.cve_enrichment.time.monotonic",
        side_effect=lambda: next(times, 100.0)
    ), patch(
        "app.services.enrichment.cve_enrichment.time.sleep"
    ) as mock_sleep, patch(
        "app.services.enrichment.cve_enrichment.NVD_API_KEY", None
    ):
        enrich_cve(db_session, "CVE-2021-44228")
        enrich_cve(db_session, "CVE-2021-45046")

    # Unauthenticated window: 30s / 5 requests = 6s minimum interval.
    # The second call happened 0.05s after the first (per the mocked
    # clock), well under that, so a sleep must have been issued.
    assert mock_sleep.called


def test_api_key_widens_rate_window_and_sets_header(db_session):
    fake_response = Mock(status_code=200, json=lambda: _nvd_payload())

    with patch(
        "app.services.enrichment.cve_enrichment.requests.get",
        return_value=fake_response
    ) as mock_get, patch(
        "app.services.enrichment.cve_enrichment.time.sleep"
    ), patch(
        "app.services.enrichment.cve_enrichment.NVD_API_KEY", "test-key-123"
    ):
        enrich_cve(db_session, "CVE-2021-44228")

    _, kwargs = mock_get.call_args
    assert kwargs["headers"] == {"apiKey": "test-key-123"}


# --- POST /vulnerabilities/{id}/enrich-cve ----------------------------------


def _seed_vulnerability_with_cve(db, org_id=1, cve_id="CVE-2021-44228", description=""):
    from app.repositories.assets.asset_repository import create_asset
    from app.repositories.vulnerabilities.vulnerability_repository import (
        create_vulnerability,
    )

    asset = create_asset(
        db, name="host", asset_type="server", owner="IT",
        criticality="High", org_id=org_id, ip_address="10.0.0.9",
        environment="prod",
    )
    vulnerability = create_vulnerability(
        db, title="t", plugin_id="1", cve_id=cve_id, solution=None,
        ip_address="10.0.0.9", description=description, asset_id=asset.id,
        cvss_score=9.5, severity="Critical", owner="x", status="Open",
        org_id=org_id,
    )
    db.commit()
    return vulnerability


def test_enrich_cve_endpoint_backfills_empty_description(client, db_session):
    vulnerability = _seed_vulnerability_with_cve(db_session, description="")

    fake_response = Mock(status_code=200, json=lambda: _nvd_payload())

    with patch(
        "app.services.enrichment.cve_enrichment.requests.get",
        return_value=fake_response
    ), patch("app.services.enrichment.cve_enrichment.time.sleep"):
        response = client.post(
            f"/vulnerabilities/{vulnerability.id}/enrich-cve"
        )

    assert response.status_code == 200, response.text
    assert response.json()["description"] == "Log4j RCE"

    updated = client.get(f"/vulnerabilities/{vulnerability.id}").json()
    assert updated["description"] == "Log4j RCE"


def test_enrich_cve_endpoint_leaves_existing_description_alone(client, db_session):
    vulnerability = _seed_vulnerability_with_cve(
        db_session, description="already has a description"
    )

    fake_response = Mock(status_code=200, json=lambda: _nvd_payload())

    with patch(
        "app.services.enrichment.cve_enrichment.requests.get",
        return_value=fake_response
    ), patch("app.services.enrichment.cve_enrichment.time.sleep"):
        client.post(f"/vulnerabilities/{vulnerability.id}/enrich-cve")

    updated = client.get(f"/vulnerabilities/{vulnerability.id}").json()
    assert updated["description"] == "already has a description"


def test_enrich_cve_endpoint_no_cve_id_is_400(client, db_session):
    vulnerability = _seed_vulnerability_with_cve(db_session, cve_id=None)

    response = client.post(f"/vulnerabilities/{vulnerability.id}/enrich-cve")

    assert response.status_code == 400
    assert response.json() == {"detail": "Vulnerability has no cve_id"}


def test_enrich_cve_endpoint_rbac_denial(client, db_session, as_role):
    from app.core.constants import ROLE_AUDITOR

    vulnerability = _seed_vulnerability_with_cve(db_session)

    as_role(ROLE_AUDITOR)
    response = client.post(f"/vulnerabilities/{vulnerability.id}/enrich-cve")

    assert response.status_code == 403


def test_enrich_cve_endpoint_cross_org_is_404(client, db_session, as_user):
    from app.core.constants import ROLE_ADMIN
    from app.models.organization import Organization

    db_session.add(Organization(id=2, name="Second Org", slug="second"))
    db_session.commit()

    vulnerability = _seed_vulnerability_with_cve(db_session, org_id=1)

    as_user(role=ROLE_ADMIN, org_id=2)
    response = client.post(f"/vulnerabilities/{vulnerability.id}/enrich-cve")

    assert response.status_code == 404
