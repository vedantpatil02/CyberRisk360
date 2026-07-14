"""
CyberRisk360

Tests for the audit trail: security-relevant actions are recorded, and
the audit-log endpoint is oversight-only with working filters.

The default authenticated user (conftest) is an admin, so it may read
the audit log.
"""

from pathlib import Path

FIXTURE_CSV = Path(__file__).parent / "fixtures" / "sample_report.csv"


def _register(client, email="a@example.com", role="analyst"):
    return client.post(
        "/register",
        json={
            # username must be unique - derive it from the email so
            # helpers registering several accounts don't collide.
            "username": email.split("@")[0],
            "email": email,
            "password": "Passw0rd!",
            "role": role,
        },
    )


def test_register_is_audited(client):
    _register(client, email="reg@example.com")

    logs = client.get("/audit-logs").json()

    entry = next(
        (l for l in logs if l["action"] == "user.register"), None
    )
    assert entry is not None
    assert entry["actor"] == "reg@example.com"
    assert entry["entity_type"] == "user"
    assert entry["detail"] == "role=analyst"


def test_login_success_and_failure_are_audited(client, reset_rate_limiter):
    _register(client, email="log@example.com")

    client.post(
        "/login",
        data={"username": "log@example.com", "password": "Passw0rd!"},
    )
    client.post(
        "/login",
        data={"username": "log@example.com", "password": "wrong"},
    )

    logs = client.get("/audit-logs").json()
    actions = [l["action"] for l in logs if l["actor"] == "log@example.com"]

    assert "login.success" in actions
    assert "login.failure" in actions


def test_audit_logs_denied_to_non_oversight_role(client, as_role):
    as_role("analyst")

    response = client.get("/audit-logs")

    assert response.status_code == 403


def test_audit_logs_filter_by_action(client):
    _register(client, email="f@example.com")

    logs = client.get("/audit-logs?action=user.register").json()

    assert logs
    assert all(l["action"] == "user.register" for l in logs)


def test_audit_logs_pagination_limit(client):
    for i in range(3):
        _register(client, email=f"p{i}@example.com")

    logs = client.get("/audit-logs?limit=2").json()

    assert len(logs) == 2


def test_import_upload_is_audited(client, db_session):
    with open(FIXTURE_CSV, "rb") as f:
        response = client.post(
            "/imports/nessus_report_upload",
            files={"file": ("sample_report.csv", f, "text/csv")},
        )
    assert response.status_code == 200

    logs = client.get("/audit-logs?action=import.upload").json()
    assert logs
    assert logs[0]["detail"].startswith("file_type=csv")


# --- persona roles (Increment C) --------------------------------------

def test_new_persona_role_can_register(client):
    # A persona from the design doc beyond the original three roles.
    response = _register(client, email="ciso@example.com", role="ciso")
    assert response.status_code == 200


def test_read_roles_include_new_personas(client, as_role):
    # A CISO (read tier) can pull an executive report...
    as_role("ciso")
    assert client.get("/reports/executive").status_code == 200


def test_oversight_role_can_read_audit_logs(client, as_role):
    # ...and a Security Manager (oversight tier) can read the audit log.
    as_role("manager")
    assert client.get("/audit-logs").status_code == 200


def test_write_only_persona_cannot_read_audit_logs(client, as_role):
    # A pentester is a write/technical role, not oversight.
    as_role("pentester")
    assert client.get("/audit-logs").status_code == 403
