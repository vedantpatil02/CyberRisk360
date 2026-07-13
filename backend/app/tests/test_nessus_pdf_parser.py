"""
CyberRisk360

Purpose:
Regression tests for the Nessus PDF finding parser.

Found via TODO.md: the parser used to take the first IP address
anywhere in the whole document and attribute every finding to it,
regardless of which host's "Vulnerabilities by Host" block the
finding actually appeared in. A single-host report (the common case,
and the only shape the real sample fixture PDF has) never surfaced
this, since there's only one IP to find either way.
"""

from app.importers.nessus_pdf_parser import extract_findings

# Real per-page footer form, confirmed against the actual sample PDF's
# extracted text: pypdf sometimes glues it directly onto the next
# finding line with no newline in between.
MULTI_HOST_CONTENT = """Vulnerabilities by Host
10.0.0.1
1 0 0 0 0
SEVERITY CVSS
CRITICAL 9.8 6.7 0.0218 11111 Finding on host A
10.0.0.1 4
10.0.0.2
0 1 0 0 0
HIGH 7.5 6.7 0.0218 22222 Finding on host B
10.0.0.2 5LOW 3.0 - - 33333 Second finding on host B
"""


def test_multi_host_findings_attributed_to_correct_host():
    findings = extract_findings(MULTI_HOST_CONTENT)

    assert len(findings) == 3

    by_plugin = {f["plugin_id"]: f["ip_address"] for f in findings}

    assert by_plugin["11111"] == "10.0.0.1"
    assert by_plugin["22222"] == "10.0.0.2"
    assert by_plugin["33333"] == "10.0.0.2"


def test_single_host_still_works():
    content = """Vulnerabilities by Host
192.168.1.5
1 0 0 0 0
CRITICAL 9.8 6.7 0.0218 11111 Finding on the only host
192.168.1.5 4
"""

    findings = extract_findings(content)

    assert len(findings) == 1
    assert findings[0]["ip_address"] == "192.168.1.5"
    assert findings[0]["severity"] == "CRITICAL"
    assert findings[0]["cvss_score"] == 9.8


def test_no_host_header_falls_back_to_unknown():
    content = "CRITICAL 9.8 6.7 0.0218 11111 Finding with no host line at all\n"

    findings = extract_findings(content)

    assert len(findings) == 1
    assert findings[0]["ip_address"] == "Unknown"


def test_asterisk_cvss_score_parsed():
    content = """10.0.0.1
LOW 2.6* - - 71049 SSH Weak MAC Algorithms Enabled
"""

    findings = extract_findings(content)

    assert len(findings) == 1
    assert findings[0]["cvss_score"] == 2.6
