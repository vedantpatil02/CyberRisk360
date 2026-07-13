"""
CyberRisk360

Purpose:
Tests for the Nessus CSV report parser.
"""

from pathlib import Path

from app.importers.nessus_csv_parser import extract_findings

FIXTURE_CSV = Path(__file__).parent / "fixtures" / "sample_report.csv"


def test_extract_findings_from_real_sample():
    content = FIXTURE_CSV.read_text()

    findings = extract_findings(content)

    # 4 data rows in the fixture, 1 is "None" risk (informational) and
    # must be skipped, leaving 3.
    assert len(findings) == 3

    by_plugin = {f["plugin_id"]: f for f in findings}

    assert by_plugin["90022"]["severity"] == "CRITICAL"
    assert by_plugin["90022"]["cvss_score"] == 9.8
    assert by_plugin["90022"]["ip_address"] == "192.168.0.169"
    assert by_plugin["90022"]["title"] == (
        "OpenSSH < 7.2 Untrusted X11 Forwarding Fallback Security Bypass"
    )

    assert by_plugin["106608"]["severity"] == "HIGH"
    assert by_plugin["90023"]["severity"] == "MEDIUM"


def test_informational_rows_are_skipped():
    content = FIXTURE_CSV.read_text()

    findings = extract_findings(content)

    assert "19506" not in {f["plugin_id"] for f in findings}


def test_rows_missing_plugin_id_or_cvss_are_skipped():
    content = (
        "Plugin ID,CVE,CVSS,Risk,Host,Protocol,Port,Name\n"
        ",CVE-2021-1,9.0,Critical,10.0.0.1,tcp,22,Missing plugin id\n"
        "111,CVE-2021-2,,Critical,10.0.0.1,tcp,22,Missing cvss\n"
        "222,CVE-2021-3,7.5,High,10.0.0.1,tcp,22,Valid row\n"
    )

    findings = extract_findings(content)

    assert len(findings) == 1
    assert findings[0]["plugin_id"] == "222"


def test_empty_content_returns_no_findings():
    assert extract_findings("") == []
    assert extract_findings("Plugin ID,CVE,CVSS,Risk,Host\n") == []
