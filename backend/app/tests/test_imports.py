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
FIXTURE_CSV = Path(__file__).parent / "fixtures" / "sample_report.csv"
FIXTURE_NESSUS = Path(__file__).parent / "fixtures" / "sample_report.nessus"

FAKE_ENRICHMENT = {
    "cve_ids": "CVE-2024-0001",
    "description": "fake enrichment description",
    "solution": "fake enrichment solution"
}

# get_plugin_enrichment returns (enrichment_dict, cache_written) -
# these tests only care about the enrichment values reaching the
# created vulnerability, so cache_written is always False (cache-hit
# shape, no commit-granularity behavior under test here).
FAKE_ENRICHMENT_RESULT = (FAKE_ENRICHMENT, False)


def _upload(client):
    with open(FIXTURE_PDF, "rb") as f:
        return client.post(
            "/imports/nessus_report_upload",
            files={"file": ("sample_nessus_report.pdf", f, "application/pdf")}
        )


def _upload_file(client, path, filename, content_type):
    with open(path, "rb") as f:
        return client.post(
            "/imports/nessus_report_upload",
            files={"file": (filename, f, content_type)}
        )


def test_upload_extracts_and_imports_findings(client, db_session):
    _import_nist_csf(db_session)

    with patch(
        "app.services.vulnerabilities.vulnerability_importer.get_plugin_enrichment",
        return_value=FAKE_ENRICHMENT_RESULT
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
        return_value=FAKE_ENRICHMENT_RESULT
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
        return_value=FAKE_ENRICHMENT_RESULT
    ):
        _upload(client)

    pending = client.get("/mappings/pending").json()
    assert len(pending) > 0


# --- CSV upload -------------------------------------------------------------


def test_csv_upload_extracts_and_imports_findings(client, db_session):
    _import_nist_csf(db_session)

    with patch(
        "app.services.vulnerabilities.vulnerability_importer.get_plugin_enrichment",
        return_value=FAKE_ENRICHMENT_RESULT
    ):
        response = _upload_file(
            client, FIXTURE_CSV, "sample_report.csv", "text/csv"
        )

    assert response.status_code == 200
    body = response.json()

    assert body["file_type"] == "csv"
    # 4 rows in the fixture, 1 is informational and skipped.
    assert body["findings_detected"] == 3
    assert body["import_result"]["created"] == 3

    vulns = client.get("/vulnerabilities").json()
    assert len(vulns) == 3


# --- .nessus XML upload ------------------------------------------------------


def test_nessus_xml_upload_extracts_and_imports_findings(client, db_session):
    _import_nist_csf(db_session)

    with patch(
        "app.services.vulnerabilities.vulnerability_importer.get_plugin_enrichment",
        return_value=FAKE_ENRICHMENT_RESULT
    ):
        response = _upload_file(
            client, FIXTURE_NESSUS, "sample_report.nessus", "application/xml"
        )

    assert response.status_code == 200
    body = response.json()

    assert body["file_type"] == "nessus"
    # 4 ReportItems in the fixture, 1 is severity="0" and skipped.
    assert body["findings_detected"] == 3
    assert body["import_result"]["created"] == 3

    vulns = client.get("/vulnerabilities").json()
    assert len(vulns) == 3


# --- validation / error handling ---------------------------------------------


def test_upload_rejects_unsupported_extension(client, tmp_path):
    bad_file = tmp_path / "malware.exe"
    bad_file.write_bytes(b"not a report")

    response = _upload_file(
        client, bad_file, "malware.exe", "application/octet-stream"
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]
    assert client.get("/vulnerabilities").json() == []


def test_malformed_csv_returns_clean_400(client, tmp_path):
    bad_csv = tmp_path / "broken.csv"
    # Not valid CSV in a way that breaks the parser's expectations -
    # a plain binary blob with a null byte, which csv.DictReader
    # chokes on.
    bad_csv.write_bytes(b"Plugin ID,CVSS,Risk\x00\xff\xfe\x00garbage")

    response = _upload_file(
        client, bad_csv, "broken.csv", "text/csv"
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Failed to parse report"}


def test_malformed_nessus_xml_returns_clean_400(client, tmp_path):
    bad_xml = tmp_path / "broken.nessus"
    bad_xml.write_text("<NessusClientData_v2><Report>not closed")

    response = _upload_file(
        client, bad_xml, "broken.nessus", "application/xml"
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Failed to parse report"}
