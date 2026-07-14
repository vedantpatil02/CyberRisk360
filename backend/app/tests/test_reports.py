"""
CyberRisk360

Tests for the reporting API: each report in JSON / HTML / PDF, the
compliance 404 path, and an RBAC denial.
"""

import pytest


def _seed_vulnerability(client, asset_id):
    """
    Create one vulnerability (and the risk it needs) so reports have
    content to render. The title carries a raw <script> tag to exercise
    HTML escaping.
    """

    risk = client.post(
        "/risks",
        json={
            "title": "Risk 1",
            "description": "d",
            "asset_id": asset_id,
            "impact": 3,
            "likelihood": 3,
            "owner": "IT",
        },
    )
    assert risk.status_code == 200

    created = client.post(
        "/vulnerabilities",
        json={
            "title": "TLS 1.0 enabled <script>",
            "description": "Legacy protocol supported.",
            "asset_id": asset_id,
            "risk_id": 1,
            "cvss_score": 7.5,
            "owner": "IT",
        },
    )
    assert created.status_code == 200


# --- Executive report --------------------------------------------------

def test_executive_report_json(client, seed_asset):
    _seed_vulnerability(client, seed_asset)

    response = client.get("/reports/executive")

    assert response.status_code == 200

    body = response.json()
    assert body["report_type"] == "Executive Summary"
    assert "overview" in body["sections"]
    assert body["sections"]["overview"]["total_vulnerabilities"] >= 1


def test_executive_report_html(client, seed_asset):
    _seed_vulnerability(client, seed_asset)

    response = client.get("/reports/executive?format=html")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Executive Summary" in response.text
    # User-controlled text must be escaped, not injected raw.
    assert "<script>" not in response.text
    # HTML reports get an inline-style CSP, never script execution.
    csp = response.headers["content-security-policy"]
    assert "style-src 'unsafe-inline'" in csp
    assert "script-src" not in csp


def test_json_report_keeps_strict_csp(client):
    response = client.get("/reports/executive")

    assert response.status_code == 200
    # JSON API responses stay locked to the maximally restrictive policy.
    assert response.headers["content-security-policy"] == "default-src 'none'"


def test_docs_csp_allows_swagger_cdn(client):
    response = client.get("/docs")

    assert response.status_code == 200
    # Regression guard: /docs must permit the Swagger UI CDN + inline
    # bootstrap, or the page renders blank.
    csp = response.headers["content-security-policy"]
    assert "https://cdn.jsdelivr.net" in csp
    assert "swagger-ui" in response.text


def test_executive_report_pdf(client, seed_asset):
    _seed_vulnerability(client, seed_asset)

    response = client.get("/reports/executive?format=pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"


# --- Technical report --------------------------------------------------

def test_technical_report_json(client, seed_asset):
    _seed_vulnerability(client, seed_asset)

    response = client.get("/reports/technical")

    assert response.status_code == 200

    body = response.json()
    assert body["report_type"] == "Technical Vulnerability Report"
    assert body["sections"]["summary"]["total_findings"] >= 1
    assert body["sections"]["findings_by_severity"]


def test_technical_report_pdf(client, seed_asset):
    _seed_vulnerability(client, seed_asset)

    response = client.get("/reports/technical?format=pdf")

    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"


# --- Compliance report -------------------------------------------------

def test_compliance_report_unknown_framework_404(client):
    response = client.get("/reports/compliance/does-not-exist")

    assert response.status_code == 404


# --- RBAC --------------------------------------------------------------

def test_reports_rbac_denies_unknown_role(client, as_role):
    as_role("guest")

    response = client.get("/reports/executive")

    assert response.status_code == 403
