"""
CyberRisk360

Purpose:
Tests for the native .nessus XML report parser.
"""

from pathlib import Path

import pytest
from defusedxml.common import EntitiesForbidden

from app.importers.nessus_xml_parser import extract_findings

FIXTURE_NESSUS = Path(__file__).parent / "fixtures" / "sample_report.nessus"


def test_extract_findings_from_real_sample():
    content = FIXTURE_NESSUS.read_text()

    findings = extract_findings(content)

    # 4 ReportItems in the fixture, 1 is severity="0" (informational)
    # and must be skipped, leaving 3.
    assert len(findings) == 3

    by_plugin = {f["plugin_id"]: f for f in findings}

    assert by_plugin["90022"]["severity"] == "CRITICAL"
    assert by_plugin["90022"]["cvss_score"] == 9.8
    assert by_plugin["90022"]["ip_address"] == "192.168.0.169"
    assert "Untrusted X11 Forwarding" in by_plugin["90022"]["title"]

    assert by_plugin["106608"]["severity"] == "HIGH"
    assert by_plugin["90023"]["severity"] == "MEDIUM"


def test_informational_severity_zero_is_skipped():
    content = FIXTURE_NESSUS.read_text()

    findings = extract_findings(content)

    assert "19506" not in {f["plugin_id"] for f in findings}


def test_multi_host_report_attributes_findings_correctly():
    content = """<?xml version="1.0"?>
<NessusClientData_v2>
  <Report name="test">
    <ReportHost name="10.0.0.1">
      <ReportItem severity="4" pluginID="111" pluginName="Finding on host A">
        <cvss_base_score>9.0</cvss_base_score>
      </ReportItem>
    </ReportHost>
    <ReportHost name="10.0.0.2">
      <ReportItem severity="3" pluginID="222" pluginName="Finding on host B">
        <cvss_base_score>7.0</cvss_base_score>
      </ReportItem>
    </ReportHost>
  </Report>
</NessusClientData_v2>"""

    findings = extract_findings(content)

    by_plugin = {f["plugin_id"]: f["ip_address"] for f in findings}

    assert by_plugin["111"] == "10.0.0.1"
    assert by_plugin["222"] == "10.0.0.2"


def test_missing_cvss_score_is_skipped():
    content = """<?xml version="1.0"?>
<NessusClientData_v2>
  <Report name="test">
    <ReportHost name="10.0.0.1">
      <ReportItem severity="4" pluginID="111" pluginName="No CVSS score"/>
    </ReportHost>
  </Report>
</NessusClientData_v2>"""

    assert extract_findings(content) == []


def test_malformed_xml_raises():
    with pytest.raises(Exception):
        extract_findings("<NessusClientData_v2><Report>not closed")


def test_xxe_attack_is_blocked():
    malicious = """<?xml version="1.0"?>
<!DOCTYPE NessusClientData_v2 [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<NessusClientData_v2>
  <Report name="&xxe;">
    <ReportHost name="10.0.0.1">
      <ReportItem severity="4" pluginID="111" pluginName="&xxe;">
        <cvss_base_score>9.0</cvss_base_score>
      </ReportItem>
    </ReportHost>
  </Report>
</NessusClientData_v2>"""

    with pytest.raises(EntitiesForbidden):
        extract_findings(malicious)
