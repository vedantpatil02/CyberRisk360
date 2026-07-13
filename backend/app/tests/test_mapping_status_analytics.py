"""
CyberRisk360

Purpose:
Confirm that compliance-scoring analytics (gap analysis, control
risk analysis, framework compliance summary) only count "approved"
vulnerability-control mappings - a "pending" (unreviewed) mapping
must not move a compliance score or risk number until a human
approves it.
"""

from app.analytics.gap_analysis import get_framework_gaps
from app.analytics.control_risk_analysis import get_control_risk_analysis
from app.services.mapping.mapping_service import review_mapping
from app.tests.test_mapping_engine import (
    _import_nist_csf,
    _persist_vulnerability
)


def _make_pending_mapping(db_session):
    """
    Import nist-csf and create a vulnerability whose title/description
    trip a keyword rule (see frameworks/nist-csf/v2.0/mapping_rules.json),
    producing pending mappings without going through the full engine
    import path.
    """

    from app.services.mapping.mapping_engine import map_vulnerability_to_controls

    _import_nist_csf(db_session)

    vulnerability = _persist_vulnerability(
        db_session,
        title="Weak SSH configuration",
        description="The SSH server allows weak ciphers.",
        severity="High"
    )

    created = map_vulnerability_to_controls(db_session, vulnerability)
    db_session.commit()

    return vulnerability, created


def test_gap_analysis_ignores_pending_mappings(db_session):
    vulnerability, created = _make_pending_mapping(db_session)

    gaps = get_framework_gaps(db_session, "nist-csf")

    affected_ids = {c["control_id"] for c in gaps["affected_controls"]}
    unaffected_ids = {c["control_id"] for c in gaps["unaffected_controls"]}

    # PR.AC-1 is one of the controls the "ssh" keyword rule maps to
    assert "PR.AC-1" in unaffected_ids
    assert "PR.AC-1" not in affected_ids


def test_gap_analysis_counts_mapping_once_approved(db_session):
    vulnerability, created = _make_pending_mapping(db_session)

    approved = next(m for m in created if m.matched_value == "ssh")
    review_mapping(db_session, approved.id, approve=True, reviewer="a@example.com")

    gaps = get_framework_gaps(db_session, "nist-csf")
    affected_ids = {c["control_id"] for c in gaps["affected_controls"]}

    assert "PR.AC-1" in affected_ids


def test_control_risk_analysis_ignores_pending_mappings(db_session):
    vulnerability, created = _make_pending_mapping(db_session)

    analysis = get_control_risk_analysis(db_session, "nist-csf")

    pr_ac_1 = next(c for c in analysis["controls"] if c["control_id"] == "PR.AC-1")

    assert pr_ac_1["risk_score"] == 0
    assert pr_ac_1["affected_vulnerabilities"] == 0


def test_control_risk_analysis_reflects_approved_mapping(db_session):
    vulnerability, created = _make_pending_mapping(db_session)

    approved = next(m for m in created if m.matched_value == "ssh")
    review_mapping(db_session, approved.id, approve=True, reviewer="a@example.com")

    analysis = get_control_risk_analysis(db_session, "nist-csf")

    pr_ac_1 = next(c for c in analysis["controls"] if c["control_id"] == "PR.AC-1")

    assert pr_ac_1["risk_score"] > 0
    assert pr_ac_1["high"] == 1


def test_framework_summary_endpoint_ignores_pending_mappings(client, db_session):
    vulnerability, created = _make_pending_mapping(db_session)

    response = client.get("/frameworks/nist-csf/summary")
    before = response.json()

    assert before["affected_controls"] == 0
    assert before["compliance_score"] == 100.0

    approved = next(m for m in created if m.matched_value == "ssh")
    review_mapping(db_session, approved.id, approve=True, reviewer="a@example.com")

    response = client.get("/frameworks/nist-csf/summary")
    after = response.json()

    assert after["affected_controls"] > 0
    assert after["compliance_score"] < 100.0
