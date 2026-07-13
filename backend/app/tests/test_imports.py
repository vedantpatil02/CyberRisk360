"""
CyberRisk360

Purpose:
Tests for the Nessus PDF report upload/import pipeline.

Mocks app.services.vulnerabilities.vulnerability_importer's imported
name for get_plugin_enrichment (not the original module - that's
where unittest.mock.patch must target for the patch to take effect)
to avoid any real network calls, while still exercising the real PDF
text extraction and finding-regex parsing against a real sample
report (app/tests/fixtures/sample_nessus_report.pdf).
"""

from pathlib import Path
from unittest.mock import patch

from app.tests.test_mapping_engine import _import_nist_csf

FIXTURE_PDF = Path(__file__).parent / "fixtures" / "sample_nessus_report.pdf"

FAKE_ENRICHMENT = {
    "cve_ids": "CVE-2024-0001",
    "description": "fake enrichment description",
    "solution": "fake enrichment solution"
}


def _upload(client):
    with open(FIXTURE_PDF, "rb") as f:
        return client.post(
            "/imports/nessus_report_upload",
            files={"file": ("sample_nessus_report.pdf", f, "application/pdf")}
        )


def test_upload_extracts_and_imports_findings(client, db_session):
    _import_nist_csf(db_session)

    with patch(
        "app.services.vulnerabilities.vulnerability_importer.get_plugin_enrichment",
        return_value=FAKE_ENRICHMENT
    ):
        response = _upload(client)

    assert response.status_code == 200
    body = response.json()

    assert body["file_type"] == "pdf"
    assert body["findings_detected"] > 0
    assert body["import_result"]["created"] == body["findings_detected"]
    assert body["import_result"]["duplicates"] == 0

    vulns = client.get("/vulnerabilities").json()
    assert len(vulns) == body["findings_detected"]
    assert vulns[0]["cve_id"] == "CVE-2024-0001"
    assert vulns[0]["solution"] == "fake enrichment solution"


def test_reupload_same_file_is_idempotent(client, db_session):
    _import_nist_csf(db_session)

    with patch(
        "app.services.vulnerabilities.vulnerability_importer.get_plugin_enrichment",
        return_value=FAKE_ENRICHMENT
    ):
        first = _upload(client)
        second = _upload(client)

    findings_detected = first.json()["findings_detected"]

    assert second.json()["import_result"]["created"] == 0
    assert second.json()["import_result"]["duplicates"] == findings_detected

    vulns = client.get("/vulnerabilities").json()
    assert len(vulns) == findings_detected


def test_upload_creates_pending_mappings(client, db_session):
    _import_nist_csf(db_session)

    with patch(
        "app.services.vulnerabilities.vulnerability_importer.get_plugin_enrichment",
        return_value=FAKE_ENRICHMENT
    ):
        _upload(client)

    pending = client.get("/mappings/pending").json()
    assert len(pending) > 0
