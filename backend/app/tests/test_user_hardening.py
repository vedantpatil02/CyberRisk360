"""
CyberRisk360

Tests for user hardening: account lockout, disabled accounts, last-login
tracking, and the self/admin password + activation endpoints.

Lockout counting is exercised at the service layer (`attempt_login`)
because the `/login` endpoint's 5/minute rate limit would otherwise cap
attempts before the lockout threshold is observable through HTTP.
"""

from datetime import datetime, timedelta, timezone

from app.core.constants import MAX_FAILED_LOGIN_ATTEMPTS
from app.repositories.users.user_repository import get_by_email
from app.services.users.user_service import (
    attempt_login,
    is_account_locked,
    LOGIN_INVALID,
    LOGIN_LOCKED,
)


def _register(client, email, password="Passw0rd!", role="analyst"):
    response = client.post(
        "/register",
        json={
            "username": "u",
            "email": email,
            "password": password,
            "role": role,
        },
    )
    assert response.status_code == 200


# --- lockout -----------------------------------------------------------

def test_account_locks_after_max_failed_attempts(client, db_session):
    _register(client, "lock@example.com")

    for _ in range(MAX_FAILED_LOGIN_ATTEMPTS):
        user, error = attempt_login(db_session, "lock@example.com", "wrong")
        assert error == LOGIN_INVALID

    assert is_account_locked(user)

    # Even the correct password is refused while the lock is active.
    user, error = attempt_login(db_session, "lock@example.com", "Passw0rd!")
    assert error == LOGIN_LOCKED


def test_login_endpoint_rejects_locked_account(
    client, db_session, reset_rate_limiter
):
    _register(client, "locked@example.com")

    user = get_by_email(db_session, "locked@example.com")
    user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
    db_session.commit()

    response = client.post(
        "/login",
        data={"username": "locked@example.com", "password": "Passw0rd!"},
    )

    assert response.status_code == 403
    assert "locked" in response.json()["detail"].lower()


def test_successful_login_resets_attempts_and_stamps_last_login(
    client, db_session, reset_rate_limiter
):
    _register(client, "ll@example.com")

    # One failed attempt, then a real login through the endpoint.
    attempt_login(db_session, "ll@example.com", "wrong")

    response = client.post(
        "/login",
        data={"username": "ll@example.com", "password": "Passw0rd!"},
    )
    assert response.status_code == 200

    db_session.expire_all()
    user = get_by_email(db_session, "ll@example.com")
    assert user.failed_login_attempts == 0
    assert user.last_login is not None


# --- disabled accounts -------------------------------------------------

def test_login_endpoint_rejects_inactive_account(
    client, db_session, reset_rate_limiter
):
    _register(client, "inactive@example.com")

    user = get_by_email(db_session, "inactive@example.com")
    user.is_active = False
    db_session.commit()

    response = client.post(
        "/login",
        data={"username": "inactive@example.com", "password": "Passw0rd!"},
    )

    assert response.status_code == 403
    assert "disabled" in response.json()["detail"].lower()


def test_admin_deactivate_then_activate(client, db_session):
    _register(client, "toggle@example.com")
    user = get_by_email(db_session, "toggle@example.com")

    assert client.post(f"/users/{user.id}/deactivate").status_code == 200
    db_session.expire_all()
    assert get_by_email(db_session, "toggle@example.com").is_active is False

    assert client.post(f"/users/{user.id}/activate").status_code == 200
    db_session.expire_all()
    assert get_by_email(db_session, "toggle@example.com").is_active is True


def test_user_management_requires_admin(client, db_session, as_role):
    _register(client, "victim@example.com")
    user = get_by_email(db_session, "victim@example.com")

    as_role("analyst")

    assert client.post(f"/users/{user.id}/deactivate").status_code == 403


# --- password change / reset ------------------------------------------

def test_change_own_password(client):
    # The overridden auth user is test@example.com; register it so the
    # lookup in the endpoint resolves to a real row.
    client.post(
        "/register",
        json={
            "username": "self",
            "email": "test@example.com",
            "password": "OldPassw0rd!",
            "role": "admin",
        },
    )

    response = client.post(
        "/users/me/change-password",
        json={
            "current_password": "OldPassw0rd!",
            "new_password": "NewPassw0rd!",
        },
    )
    assert response.status_code == 200


def test_change_own_password_wrong_current(client):
    client.post(
        "/register",
        json={
            "username": "self",
            "email": "test@example.com",
            "password": "OldPassw0rd!",
            "role": "admin",
        },
    )

    response = client.post(
        "/users/me/change-password",
        json={
            "current_password": "WRONG",
            "new_password": "NewPassw0rd!",
        },
    )
    assert response.status_code == 400


def test_change_password_enforces_min_length(client):
    client.post(
        "/register",
        json={
            "username": "self",
            "email": "test@example.com",
            "password": "OldPassw0rd!",
            "role": "admin",
        },
    )

    response = client.post(
        "/users/me/change-password",
        json={"current_password": "OldPassw0rd!", "new_password": "short"},
    )
    assert response.status_code == 422


def test_admin_reset_password(client, db_session, reset_rate_limiter):
    _register(client, "target@example.com", password="OldPassw0rd!")
    user = get_by_email(db_session, "target@example.com")

    response = client.post(
        f"/users/{user.id}/reset-password",
        json={"new_password": "Reset1234!"},
    )
    assert response.status_code == 200

    # The new password now authenticates.
    login = client.post(
        "/login",
        data={"username": "target@example.com", "password": "Reset1234!"},
    )
    assert login.status_code == 200
