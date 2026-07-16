"""
CyberRisk360

Purpose:
Tests for CWE mapping - the curated static catalog
(app/services/enrichment/cwe_catalog.py) and the
GET /vulnerabilities/{id}/cwe-info endpoint, which resolves a
vulnerability's CWE from the NVD enrichment cache first, falling back
to the mapping engine's own title/description regex extraction. No
network calls anywhere in this sprint's runtime code, so nothing here
needs to mock requests.get.

Also covers CAPEC + MITRE ATT&CK Mapping (app/services/enrichment/
capec_catalog.py), additive to this same endpoint - see its module
docstring for why one dataset covers both.
"""

from datetime import datetime, timezone

from app.models.nvd_enrichment_cache import NvdEnrichmentCache
from app.repositories.vulnerabilities.vulnerability_repository import (
    create_vulnerability,
)
from app.services.enrichment.cwe_catalog import get_cwe_info
from app.services.enrichment.capec_catalog import get_capec_for_cwe


def _create_asset(client):
    response = client.post("/assets", json={
        "name": "web-01", "asset_type": "server", "owner": "IT",
        "criticality": "High", "environment": "prod"
    })
    assert response.status_code == 200
    return client.get("/assets").json()[0]["id"]


def _create_vulnerability(db, client, *, cve_id=None, title="Finding", description="d"):
    asset_id = _create_asset(client)

    vulnerability = create_vulnerability(
        db,
        title=title, description=description, cvss_score=7.5,
        severity="High", status="Open", asset_id=asset_id,
        cve_id=cve_id, org_id=1,
    )
    db.commit()

    return vulnerability.id


# --- catalog lookup ------------------------------------------------------


def test_get_cwe_info_known_id():
    info = get_cwe_info("CWE-287")

    assert info["name"] == "Improper Authentication"
    assert "identity" in info["description"]


def test_get_cwe_info_unknown_id():
    assert get_cwe_info("CWE-999999") is None


# --- endpoint --------------------------------------------------------------


def test_cwe_info_endpoint_uses_nvd_cache(client, db_session):
    vulnerability_id = _create_vulnerability(
        db_session, client, cve_id="CVE-2021-44228", title="Log4Shell", description="d"
    )

    db_session.add(NvdEnrichmentCache(
        cve_id="CVE-2021-44228",
        cwe_id="CWE-502",
        status="ok",
        fetched_at=datetime.now(timezone.utc),
    ))
    db_session.commit()

    response = client.get(f"/vulnerabilities/{vulnerability_id}/cwe-info")

    assert response.status_code == 200
    body = response.json()
    assert body["cwe_id"] == "CWE-502"
    assert body["name"] == "Deserialization of Untrusted Data"
    assert body["url"] == "https://cwe.mitre.org/data/definitions/502.html"
    # CWE-502's curated CAPEC pattern (Object Injection) has no real
    # ATT&CK linkage in MITRE's own data - honestly empty, not padded.
    assert body["capec"]["capec_id"] == "CAPEC-586"
    assert body["capec"]["attack_techniques"] == []


def test_cwe_info_endpoint_falls_back_to_regex(client, db_session):
    vulnerability_id = _create_vulnerability(
        db_session, client,
        cve_id=None,
        title="Reflected XSS in search box",
        description="Affected by CWE-79 - user input rendered unescaped.",
    )

    response = client.get(f"/vulnerabilities/{vulnerability_id}/cwe-info")

    assert response.status_code == 200
    body = response.json()
    assert body["cwe_id"] == "CWE-79"
    assert "Cross-site Scripting" in body["name"]


def test_cwe_info_endpoint_prefers_nvd_cache_over_regex(client, db_session):
    # Title/description mentions CWE-79, but NVD enrichment (the
    # authoritative source) says CWE-89 - the cache should win.
    vulnerability_id = _create_vulnerability(
        db_session, client, cve_id="CVE-2020-00000",
        title="Mentions CWE-79 in passing", description="d",
    )

    db_session.add(NvdEnrichmentCache(
        cve_id="CVE-2020-00000",
        cwe_id="CWE-89",
        status="ok",
        fetched_at=datetime.now(timezone.utc),
    ))
    db_session.commit()

    response = client.get(f"/vulnerabilities/{vulnerability_id}/cwe-info")

    assert response.json()["cwe_id"] == "CWE-89"


def test_cwe_info_endpoint_ignores_failed_nvd_entry(client, db_session):
    vulnerability_id = _create_vulnerability(
        db_session, client, cve_id="CVE-2020-11111",
        title="No weakness mentioned here", description="d",
    )

    db_session.add(NvdEnrichmentCache(
        cve_id="CVE-2020-11111",
        cwe_id=None,
        status="failed",
        fetched_at=datetime.now(timezone.utc),
    ))
    db_session.commit()

    response = client.get(f"/vulnerabilities/{vulnerability_id}/cwe-info")

    assert response.json() == {
        "cwe_id": None, "name": None, "description": None, "url": None,
        "capec": None,
    }


def test_cwe_info_endpoint_no_cwe_found(client, db_session):
    vulnerability_id = _create_vulnerability(
        db_session, client, cve_id=None,
        title="Generic finding", description="Nothing weakness-related here.",
    )

    response = client.get(f"/vulnerabilities/{vulnerability_id}/cwe-info")

    assert response.status_code == 200
    assert response.json() == {
        "cwe_id": None, "name": None, "description": None, "url": None,
        "capec": None,
    }


def test_cwe_info_endpoint_real_but_uncatalogued_cwe(client, db_session):
    vulnerability_id = _create_vulnerability(
        db_session, client, cve_id=None,
        title="Weird one", description="Related to CWE-77777 somehow.",
    )

    response = client.get(f"/vulnerabilities/{vulnerability_id}/cwe-info")

    body = response.json()
    assert body["cwe_id"] == "CWE-77777"
    assert body["name"] is None
    assert body["url"] == "https://cwe.mitre.org/data/definitions/77777.html"
    assert body["capec"] is None


# --- CAPEC + MITRE ATT&CK ---------------------------------------------


def test_get_capec_for_cwe_known_id():
    capec = get_capec_for_cwe("CWE-287")

    assert capec["capec_id"] == "CAPEC-115"
    assert capec["name"] == "Authentication Bypass"
    assert capec["url"] == "https://capec.mitre.org/data/definitions/115.html"
    assert capec["attack_techniques"] == [{
        "id": "T1548",
        "name": "Abuse Elevation Control Mechanism",
        "url": "https://attack.mitre.org/techniques/T1548/",
    }]


def test_get_capec_for_cwe_unknown_id():
    assert get_capec_for_cwe("CWE-999999") is None


def test_get_capec_for_cwe_formats_subtechnique_url():
    # T1110.001 -> .../techniques/T1110/001/ (MITRE's real sub-technique
    # URL scheme uses a slash, not the dot the id itself uses).
    capec = get_capec_for_cwe("CWE-521")

    technique = capec["attack_techniques"][0]
    assert technique["id"] == "T1110.001"
    assert technique["url"] == "https://attack.mitre.org/techniques/T1110/001/"


def test_cwe_info_endpoint_includes_capec_with_attack_techniques(client, db_session):
    vulnerability_id = _create_vulnerability(
        db_session, client, cve_id="CVE-2020-22222",
        title="Auth bypass finding", description="d",
    )

    db_session.add(NvdEnrichmentCache(
        cve_id="CVE-2020-22222",
        cwe_id="CWE-287",
        status="ok",
        fetched_at=datetime.now(timezone.utc),
    ))
    db_session.commit()

    response = client.get(f"/vulnerabilities/{vulnerability_id}/cwe-info")

    capec = response.json()["capec"]
    assert capec["capec_id"] == "CAPEC-115"
    assert len(capec["attack_techniques"]) == 1
    assert capec["attack_techniques"][0]["id"] == "T1548"


def test_cwe_info_endpoint_not_found(client):
    response = client.get("/vulnerabilities/999999/cwe-info")

    assert response.status_code == 404


def test_cwe_info_endpoint_requires_read_role(client, db_session, as_role):
    vulnerability_id = _create_vulnerability(
        db_session, client, cve_id=None, title="t", description="d",
    )

    as_role("pentester")

    response = client.get(f"/vulnerabilities/{vulnerability_id}/cwe-info")

    assert response.status_code == 403
