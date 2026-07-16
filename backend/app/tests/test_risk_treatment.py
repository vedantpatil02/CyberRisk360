"""
CyberRisk360

Purpose:
Tests for the Risk Treatment + Approval workflow: propose
(mitigate/accept/transfer/avoid), approve/reject, RBAC separation of
duties (propose = COMPLIANCE_ROLES, approve/reject = OVERSIGHT_ROLES),
and the treatment history trail.
"""

import pytest

from app.core.constants import (
    RISK_STATUS_OPEN,
    RISK_STATUS_UNDER_REVIEW,
    RISK_STATUS_MITIGATED,
    RISK_STATUS_ACCEPTED,
    RISK_STATUS_TRANSFERRED,
    RISK_STATUS_AVOIDED,
    RISK_APPROVAL_PENDING,
    RISK_APPROVAL_APPROVED,
    RISK_APPROVAL_REJECTED,
)


def _create_asset(client):
    response = client.post("/assets", json={
        "name": "web-01", "asset_type": "server", "owner": "IT",
        "criticality": "High", "environment": "prod"
    })
    assert response.status_code == 200
    return client.get("/assets").json()[0]["id"]


def _create_risk(client):
    asset_id = _create_asset(client)

    client.post("/risks", json={
        "title": "Risk 1", "description": "d", "asset_id": asset_id,
        "impact": 4, "likelihood": 3, "owner": "IT"
    })

    return client.get("/risks").json()[0]["id"]


def test_propose_treatment_happy_path(client):
    risk_id = _create_risk(client)

    response = client.post(
        f"/risks/{risk_id}/treatment",
        json={"treatment_type": "mitigate", "justification": "patch it"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == RISK_STATUS_UNDER_REVIEW
    assert body["approval_status"] == RISK_APPROVAL_PENDING
    assert body["treatment_type"] == "mitigate"
    assert body["treatment_justification"] == "patch it"


def test_propose_treatment_not_found(client):
    response = client.post(
        "/risks/999999/treatment",
        json={"treatment_type": "mitigate", "justification": "x"}
    )

    assert response.status_code == 404


def test_propose_treatment_invalid_type(client):
    risk_id = _create_risk(client)

    response = client.post(
        f"/risks/{risk_id}/treatment",
        json={"treatment_type": "ignore", "justification": "x"}
    )

    assert response.status_code == 422


def test_propose_treatment_rbac_denied(client, as_role):
    risk_id = _create_risk(client)

    as_role("pentester")

    response = client.post(
        f"/risks/{risk_id}/treatment",
        json={"treatment_type": "mitigate", "justification": "x"}
    )

    assert response.status_code == 403


def test_propose_treatment_on_closed_risk(client):
    risk_id = _create_risk(client)

    close_response = client.patch(f"/risks/{risk_id}/close")
    assert close_response.status_code == 200

    response = client.post(
        f"/risks/{risk_id}/treatment",
        json={"treatment_type": "mitigate", "justification": "x"}
    )

    assert response.status_code == 400


@pytest.mark.parametrize(
    "treatment_type,expected_status",
    [
        ("mitigate", RISK_STATUS_MITIGATED),
        ("accept", RISK_STATUS_ACCEPTED),
        ("transfer", RISK_STATUS_TRANSFERRED),
        ("avoid", RISK_STATUS_AVOIDED),
    ]
)
def test_approve_treatment_all_types(client, treatment_type, expected_status):
    risk_id = _create_risk(client)

    client.post(
        f"/risks/{risk_id}/treatment",
        json={"treatment_type": treatment_type, "justification": "x"}
    )

    response = client.patch(
        f"/risks/{risk_id}/treatment/approve",
        json={"note": "signed off"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == expected_status
    assert body["approval_status"] == RISK_APPROVAL_APPROVED
    assert body["approved_by"] == "test@example.com"
    assert body["approved_at"] is not None


def test_approve_treatment_rbac_denied(client, as_role):
    risk_id = _create_risk(client)

    client.post(
        f"/risks/{risk_id}/treatment",
        json={"treatment_type": "mitigate", "justification": "x"}
    )

    # analyst can propose (COMPLIANCE_ROLES) but not approve
    # (OVERSIGHT_ROLES) - separation of duties.
    as_role("analyst")

    response = client.patch(f"/risks/{risk_id}/treatment/approve")

    assert response.status_code == 403


def test_reject_treatment_reverts_to_open(client):
    risk_id = _create_risk(client)

    client.post(
        f"/risks/{risk_id}/treatment",
        json={"treatment_type": "mitigate", "justification": "x"}
    )

    response = client.patch(
        f"/risks/{risk_id}/treatment/reject",
        json={"note": "not convinced"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == RISK_STATUS_OPEN
    assert body["approval_status"] == RISK_APPROVAL_REJECTED


def test_review_treatment_without_pending_treatment(client):
    risk_id = _create_risk(client)

    response = client.patch(f"/risks/{risk_id}/treatment/approve")

    assert response.status_code == 400


def test_review_treatment_not_found(client):
    response = client.patch("/risks/999999/treatment/approve")

    assert response.status_code == 404


def test_treatment_history_endpoint(client):
    risk_id = _create_risk(client)

    client.post(
        f"/risks/{risk_id}/treatment",
        json={"treatment_type": "accept", "justification": "x"}
    )
    client.patch(f"/risks/{risk_id}/treatment/approve")

    response = client.get(f"/risks/{risk_id}/treatment/history")

    assert response.status_code == 200
    actions = [entry["action"] for entry in response.json()]
    assert actions == ["proposed", "approved"]


def test_treatment_history_endpoint_not_found(client):
    response = client.get("/risks/999999/treatment/history")

    assert response.status_code == 404
