"""
CyberRisk360

Purpose:
Rate limiting configuration.

In-memory storage (slowapi's default) - fine for the current
single-instance deployment (docker-compose.yml runs one backend
container). If this ever scales to multiple replicas, this needs a
shared backend (e.g. Redis) instead, since each process would
otherwise track limits independently.

The rate-limit key is the client IP resolved by `app/core/net.py`,
which honors `X-Forwarded-For` when `TRUST_PROXY_HEADERS` is enabled -
so behind a trusted proxy, limits are keyed on the real client rather
than the proxy's single address.
"""

from slowapi import Limiter

from app.core.net import get_client_ip

limiter = Limiter(
    key_func=get_client_ip,
    default_limits=["100/minute"]
)
