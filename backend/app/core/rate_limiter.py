"""
CyberRisk360

Purpose:
Rate limiting configuration.

In-memory storage (slowapi's default) - fine for the current
single-instance deployment (docker-compose.yml runs one backend
container). If this ever scales to multiple replicas, this needs a
shared backend (e.g. Redis) instead, since each process would
otherwise track limits independently. get_remote_address reads
request.client.host directly, which is correct with no reverse proxy
in front; revisit (trust X-Forwarded-For) if one is added later.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"]
)
