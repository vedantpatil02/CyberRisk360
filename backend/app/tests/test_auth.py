"""
CyberRisk360

Purpose:
Tests for authentication and user registration.

POST /login is NOT covered by conftest.py's get_current_user override
(it doesn't depend on get_current_user at all - it calls
authenticate_user directly and issues a real JWT), so these tests
exercise the real login/registration logic, not the test-only bypass.
"""

from app.services.auth.auth import decode_access_token


def _register(client, email="user@example.com", password="Passw0rd!", role="admin"):
    return client.post("/register", json={
        "username": "user1", "email": email, "password": password, "role": role
    })


def test_me_returns_overridden_user(client):
    response = client.get("/me")

    assert response.status_code == 200
    assert response.json() == {"sub": "test@example.com", "role": "admin"}


def test_register_and_login_happy_path(client):
    register_response = _register(client)
    assert register_response.status_code == 200
    assert register_response.json() == {"message": "User created successfully"}

    login_response = client.post("/login", data={
        "username": "user@example.com", "password": "Passw0rd!"
    })

    assert login_response.status_code == 200
    body = login_response.json()
    assert body["token_type"] == "bearer"

    claims = decode_access_token(body["access_token"])
    assert claims["sub"] == "user@example.com"
    assert claims["role"] == "admin"


def test_login_wrong_password(client):
    _register(client)

    response = client.post("/login", data={
        "username": "user@example.com", "password": "wrong"
    })

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_login_nonexistent_user(client):
    response = client.post("/login", data={
        "username": "nobody@example.com", "password": "x"
    })

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_register_duplicate_email(client):
    _register(client)

    response = _register(client)

    assert response.status_code == 409
    assert response.json() == {"detail": "User already exists"}


def test_register_invalid_role(client):
    response = _register(client, email="other@example.com", role="superuser")

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid role"}


def test_login_rate_limited_after_five_attempts(client, reset_rate_limiter):
    for _ in range(5):
        response = client.post("/login", data={
            "username": "nobody@example.com", "password": "wrong"
        })
        assert response.status_code == 401

    response = client.post("/login", data={
        "username": "nobody@example.com", "password": "wrong"
    })

    assert response.status_code == 429
