"""
CyberRisk360

Tests for request correlation (X-Request-ID) and the client-IP
resolution policy (X-Forwarded-For only when trusted).
"""

from types import SimpleNamespace

import app.core.net as net


class _FakeRequest:
    def __init__(self, headers=None, host="1.2.3.4"):
        self.headers = headers or {}
        self.client = SimpleNamespace(host=host) if host else None


def test_client_ip_uses_socket_peer_by_default(monkeypatch):
    monkeypatch.setattr(net, "TRUST_PROXY_HEADERS", False)

    request = _FakeRequest(
        headers={"x-forwarded-for": "9.9.9.9"}, host="1.2.3.4"
    )

    # X-Forwarded-For is ignored when proxies aren't trusted.
    assert net.get_client_ip(request) == "1.2.3.4"


def test_client_ip_trusts_forwarded_for_when_enabled(monkeypatch):
    monkeypatch.setattr(net, "TRUST_PROXY_HEADERS", True)

    request = _FakeRequest(
        headers={"x-forwarded-for": "9.9.9.9, 10.0.0.1"}, host="1.2.3.4"
    )

    # Left-most entry is the original client.
    assert net.get_client_ip(request) == "9.9.9.9"


def test_request_id_header_is_set(client):
    response = client.get("/health")

    assert response.headers.get("x-request-id")


def test_inbound_request_id_is_echoed(client):
    response = client.get(
        "/health", headers={"X-Request-ID": "corr-123"}
    )

    assert response.headers["x-request-id"] == "corr-123"
