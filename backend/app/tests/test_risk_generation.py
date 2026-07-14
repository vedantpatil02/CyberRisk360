"""
CyberRisk360

Tests for automatic per-asset risk generation: derivation of
impact/likelihood, owner assignment, vulnerability linkage, idempotency,
and that manual risks are never touched. Plus the import and backfill
wiring.
"""

from pathlib import Path

from app.repositories.assets.asset_repository import create_asset
from app.repositories.vulnerabilities.vulnerability_repository import (
    create_vulnerability,
    get_by_asset,
)
from app.repositories.risks.risk_repository import (
    create_risk,
    get_risk,
    get_all_risks,
)
from app.services.risks.risk_generation import generate_risk_for_asset

FIXTURE_CSV = Path(__file__).parent / "fixtures" / "sample_report.csv"


def _asset(db, criticality="Medium", owner="Imported", ip="10.0.0.1"):
    return create_asset(
        db,
        name=f"Host-{ip}",
        asset_type="server",
        owner=owner,
        criticality=criticality,
        ip_address=ip,
        environment="prod",
    )


def _vuln(db, asset_id, severity="High", cvss=7.5):
    v = create_vulnerability(
        db,
        title="Finding",
        plugin_id=None,
        cve_id=None,
        solution=None,
        ip_address="10.0.0.1",
        description="d",
        asset_id=asset_id,
        cvss_score=cvss,
        severity=severity,
        owner="Imported",
        status="Open",
    )
    db.commit()
    return v


# --- derivation & linkage ---------------------------------------------

def test_generate_derives_impact_likelihood_and_links(client, db_session):
    asset = _asset(db_session, criticality="Medium")
    _vuln(db_session, asset.id, severity="Critical")
    _vuln(db_session, asset.id, severity="Low")

    risk = generate_risk_for_asset(db_session, asset)

    assert risk.source == "auto"
    assert risk.impact == 3        # Medium criticality
    assert risk.likelihood == 5    # worst severity is Critical
    assert risk.risk_score == 15
    assert risk.risk_level == "High"
    assert risk.owner == "Imported"

    for v in get_by_asset(db_session, asset.id):
        assert v.risk_id == risk.id


def test_owner_falls_back_to_unassigned_when_blank(client, db_session):
    asset = _asset(db_session, owner="")
    _vuln(db_session, asset.id)

    risk = generate_risk_for_asset(db_session, asset)

    assert risk.owner == "Unassigned"


def test_no_risk_when_asset_has_no_vulnerabilities(client, db_session):
    asset = _asset(db_session)

    assert generate_risk_for_asset(db_session, asset) is None


# --- idempotency & manual isolation -----------------------------------

def test_generation_is_idempotent(client, db_session):
    asset = _asset(db_session)
    _vuln(db_session, asset.id)

    first = generate_risk_for_asset(db_session, asset)
    second = generate_risk_for_asset(db_session, asset)

    assert first.id == second.id
    autos = [r for r in get_all_risks(db_session) if r.source == "auto"]
    assert len(autos) == 1


def test_manual_risk_is_not_touched(client, db_session):
    asset = _asset(db_session)
    _vuln(db_session, asset.id)

    manual = create_risk(
        db_session,
        title="Manual risk",
        description="hand-written",
        asset_id=asset.id,
        impact=2,
        likelihood=2,
        risk_score=4,
        risk_level="Low",
        owner="Alice",
        source="manual",
    )

    generate_risk_for_asset(db_session, asset)

    still = get_risk(db_session, manual.id)
    assert still.owner == "Alice"
    assert still.source == "manual"
    assert still.title == "Manual risk"


# --- endpoint & import wiring -----------------------------------------

def test_generate_endpoint_backfills(client, db_session):
    asset = _asset(db_session)
    _vuln(db_session, asset.id)

    response = client.post("/risks/generate")

    assert response.status_code == 200
    assert response.json()["risks_generated"] == 1

    risks = client.get("/risks").json()
    assert any(r["source"] == "auto" for r in risks)


def test_generate_endpoint_requires_write_role(client, as_role):
    as_role("auditor")

    assert client.post("/risks/generate").status_code == 403


def test_import_auto_generates_and_links_risk(client, db_session):
    with open(FIXTURE_CSV, "rb") as f:
        response = client.post(
            "/imports/nessus_report_upload",
            files={"file": ("sample_report.csv", f, "text/csv")},
        )
    assert response.status_code == 200

    risks = client.get("/risks").json()
    autos = [r for r in risks if r["source"] == "auto"]
    assert autos

    # Every imported vulnerability is linked to a risk.
    vulns = client.get("/vulnerabilities").json()
    assert vulns
    assert all(v["risk_id"] is not None for v in vulns)
