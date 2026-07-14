"""
CyberRisk360

Purpose:
Tests for the generic vulnerability-control mapping engine: rule
loading/merging, CVE/CWE/plugin_id/keyword matchers, confidence
scoring, persisted mapping + history creation, manual approval, and
the review API endpoints.
"""

from types import SimpleNamespace

from app.core.constants import (
    FRAMEWORKS_DIR,
    MATCH_TYPE_CVE,
    MATCH_TYPE_CWE,
    MATCH_TYPE_PLUGIN_ID,
    MATCH_TYPE_KEYWORD,
    MAPPING_STATUS_PENDING,
    MAPPING_STATUS_APPROVED,
    MAPPING_STATUS_REJECTED
)
from app.models.vulnerability import Vulnerability
from app.services.frameworks.framework_loader import (
    load_framework,
    discover_frameworks
)
from app.services.frameworks.framework_importer import import_framework
from app.services.mapping.mapping_engine import (
    load_rules,
    find_candidate_matches,
    map_vulnerability_to_controls
)
from app.services.mapping.mapping_service import (
    list_mappings_for_vulnerability,
    list_pending_mappings,
    get_mapping_history,
    review_mapping
)
from app.repositories.vulnerability_control_mappings.mapping_repository import (
    get_by_vulnerability
)


FAKE_RULES = {
    "cve": {"cve-2021-44228": ["ID.RA-1"]},
    "cwe": {"cwe-79": ["PR.DS-1"]},
    "plugin_id": {"12345": ["PR.AC-3"]},
    "keyword": {"ssh": ["PR.AC-1"]}
}


def _fake_vulnerability(**overrides):
    defaults = {
        "id": 1,
        "title": "",
        "description": "",
        "cve_id": None,
        "plugin_id": None
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _import_nist_csf(db):
    discovered = discover_frameworks(FRAMEWORKS_DIR)
    controls = load_framework(discovered["nist-csf"]["framework_path"])
    metadata = load_framework(discovered["nist-csf"]["metadata_path"])
    import_framework(metadata, controls, db)


def _persist_vulnerability(db, **overrides):
    defaults = {
        "title": "Weak SSH configuration",
        "description": "The SSH server allows weak ciphers.",
        "cve_id": None,
        "plugin_id": None,
        "cvss_score": 5.0,
        "severity": "Medium",
        "org_id": 1
    }
    defaults.update(overrides)

    vulnerability = Vulnerability(**defaults)
    db.add(vulnerability)
    db.flush()

    return vulnerability


# --- Pure matcher tests (no DB) ---------------------------------------


def test_find_candidate_matches_cve():
    vulnerability = _fake_vulnerability(cve_id="CVE-2021-44228")

    matches = find_candidate_matches(vulnerability, FAKE_RULES)

    assert (MATCH_TYPE_CVE, "CVE-2021-44228", "ID.RA-1") in matches


def test_find_candidate_matches_cwe_extracted_from_description():
    vulnerability = _fake_vulnerability(
        description="Stored XSS (CWE-79) found in the comments field."
    )

    matches = find_candidate_matches(vulnerability, FAKE_RULES)

    assert (MATCH_TYPE_CWE, "CWE-79", "PR.DS-1") in matches


def test_find_candidate_matches_plugin_id():
    vulnerability = _fake_vulnerability(plugin_id="12345")

    matches = find_candidate_matches(vulnerability, FAKE_RULES)

    assert (MATCH_TYPE_PLUGIN_ID, "12345", "PR.AC-3") in matches


def test_find_candidate_matches_keyword():
    vulnerability = _fake_vulnerability(title="Outdated SSH daemon")

    matches = find_candidate_matches(vulnerability, FAKE_RULES)

    assert (MATCH_TYPE_KEYWORD, "ssh", "PR.AC-1") in matches


def test_find_candidate_matches_no_match_returns_empty():
    vulnerability = _fake_vulnerability(title="Completely unrelated finding")

    assert find_candidate_matches(vulnerability, FAKE_RULES) == []


def test_find_candidate_matches_orders_by_confidence():
    """
    CVE/plugin_id/CWE are more specific than a free-text keyword
    match, so when a vulnerability trips more than one rule type the
    higher-confidence match must come first (the engine relies on
    this order to decide which match "wins" a given control).
    """

    vulnerability = _fake_vulnerability(
        cve_id="CVE-2021-44228",
        title="Outdated SSH daemon"
    )

    matches = find_candidate_matches(vulnerability, FAKE_RULES)
    match_types = [match[0] for match in matches]

    assert match_types.index(MATCH_TYPE_CVE) < match_types.index(MATCH_TYPE_KEYWORD)


def test_load_rules_merges_frameworks_and_skips_empty():
    """
    load_rules() must merge every framework's mapping_rules.json
    (nist-csf and owasp-top10 have real content; cis/iso27001/
    owasp-asvs are still empty placeholders) without raising, and
    without ever referencing a framework by name.
    """

    rules = load_rules()

    assert "ID.RA-1" in rules["cve"]["cve-2021-44228"]
    assert "A03" in rules["cwe"]["cwe-79"]


# --- Engine + DB tests --------------------------------------------------


def test_map_vulnerability_to_controls_creates_pending_mapping_with_history(db_session):
    _import_nist_csf(db_session)

    vulnerability = _persist_vulnerability(db_session)

    created = map_vulnerability_to_controls(db_session, vulnerability)
    db_session.commit()

    assert len(created) > 0

    mapping = created[0]
    assert mapping.status == MAPPING_STATUS_PENDING
    assert mapping.confidence_score is not None
    assert mapping.match_type == MATCH_TYPE_KEYWORD

    history = get_mapping_history(db_session, mapping.id)
    assert len(history) == 1
    assert history[0].action == "created"
    assert history[0].new_status == MAPPING_STATUS_PENDING


def test_map_vulnerability_to_controls_is_idempotent(db_session):
    _import_nist_csf(db_session)

    vulnerability = _persist_vulnerability(db_session)

    first_pass = map_vulnerability_to_controls(db_session, vulnerability)
    db_session.commit()

    second_pass = map_vulnerability_to_controls(db_session, vulnerability)
    db_session.commit()

    assert len(first_pass) > 0
    assert second_pass == []
    assert len(get_by_vulnerability(db_session, vulnerability.id)) == len(first_pass)


def test_map_vulnerability_to_controls_matches_cve(db_session):
    _import_nist_csf(db_session)

    vulnerability = _persist_vulnerability(
        db_session,
        title="Remote code execution",
        description="Log4Shell",
        cve_id="CVE-2021-44228,CVE-2021-45046"
    )

    created = map_vulnerability_to_controls(db_session, vulnerability)
    db_session.commit()

    match_types = {mapping.match_type for mapping in created}
    assert MATCH_TYPE_CVE in match_types


# --- Review workflow tests -----------------------------------------------


def test_review_mapping_approve(db_session):
    _import_nist_csf(db_session)

    vulnerability = _persist_vulnerability(db_session)
    created = map_vulnerability_to_controls(db_session, vulnerability)
    db_session.commit()

    mapping = review_mapping(
        db_session,
        created[0].id,
        approve=True,
        reviewer="analyst@example.com",
        note="Confirmed manually"
    )

    assert mapping.status == MAPPING_STATUS_APPROVED
    assert mapping.reviewed_by == "analyst@example.com"
    assert mapping.reviewed_at is not None

    history = get_mapping_history(db_session, mapping.id)
    assert history[-1].action == "approved"
    assert history[-1].note == "Confirmed manually"


def test_review_mapping_reject(db_session):
    _import_nist_csf(db_session)

    vulnerability = _persist_vulnerability(db_session)
    created = map_vulnerability_to_controls(db_session, vulnerability)
    db_session.commit()

    mapping = review_mapping(
        db_session,
        created[0].id,
        approve=False,
        reviewer="analyst@example.com"
    )

    assert mapping.status == MAPPING_STATUS_REJECTED

    history = get_mapping_history(db_session, mapping.id)
    assert history[-1].action == "rejected"


def test_review_mapping_not_found_returns_none(db_session):
    assert review_mapping(db_session, 999999, approve=True) is None


def test_list_pending_mappings_excludes_reviewed(db_session):
    _import_nist_csf(db_session)

    vulnerability = _persist_vulnerability(db_session)
    created = map_vulnerability_to_controls(db_session, vulnerability)
    db_session.commit()

    review_mapping(db_session, created[0].id, approve=True, reviewer="a@example.com")

    pending = list_pending_mappings(db_session)
    pending_ids = {mapping.id for mapping in pending}

    assert created[0].id not in pending_ids


def test_list_mappings_for_vulnerability(db_session):
    _import_nist_csf(db_session)

    vulnerability = _persist_vulnerability(db_session)
    created = map_vulnerability_to_controls(db_session, vulnerability)
    db_session.commit()

    mappings = list_mappings_for_vulnerability(db_session, vulnerability.id)

    assert {mapping.id for mapping in mappings} == {mapping.id for mapping in created}


# --- API tests -------------------------------------------------------------


def test_pending_mappings_endpoint(client, db_session):
    _import_nist_csf(db_session)
    vulnerability = _persist_vulnerability(db_session)
    created = map_vulnerability_to_controls(db_session, vulnerability)
    db_session.commit()

    response = client.get("/mappings/pending")

    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert created[0].id in ids


def test_vulnerability_mappings_endpoint(client, db_session):
    _import_nist_csf(db_session)
    vulnerability = _persist_vulnerability(db_session)
    map_vulnerability_to_controls(db_session, vulnerability)
    db_session.commit()

    response = client.get(f"/vulnerabilities/{vulnerability.id}/mappings")

    assert response.status_code == 200
    assert len(response.json()) > 0


def test_approve_mapping_endpoint(client, db_session):
    _import_nist_csf(db_session)
    vulnerability = _persist_vulnerability(db_session)
    created = map_vulnerability_to_controls(db_session, vulnerability)
    db_session.commit()

    response = client.patch(
        f"/mappings/{created[0].id}/approve",
        json={"note": "looks right"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == MAPPING_STATUS_APPROVED

    history_response = client.get(f"/mappings/{created[0].id}/history")
    actions = [entry["action"] for entry in history_response.json()]
    assert actions == ["created", "approved"]


def test_reject_mapping_endpoint(client, db_session):
    _import_nist_csf(db_session)
    vulnerability = _persist_vulnerability(db_session)
    created = map_vulnerability_to_controls(db_session, vulnerability)
    db_session.commit()

    response = client.patch(f"/mappings/{created[0].id}/reject")

    assert response.status_code == 200
    assert response.json()["status"] == MAPPING_STATUS_REJECTED


def test_approve_mapping_not_found(client):
    response = client.patch("/mappings/999999/approve")

    assert response.status_code == 404
