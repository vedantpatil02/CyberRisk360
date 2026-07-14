"""
CyberRisk360

Purpose:
Resolve the client IP for a request in one place, so rate limiting and
the audit trail agree and the reverse-proxy policy is configured once.
"""

from app.core.config import TRUST_PROXY_HEADERS


def get_client_ip(request):
    """
    Return the best-known client IP for `request`.

    With `TRUST_PROXY_HEADERS` enabled, use the left-most entry of
    `X-Forwarded-For` (the original client, as set by a trusted proxy);
    otherwise use the socket peer address. Falls back to None when the
    client is unknown.
    """

    if request is None:
        return None

    if TRUST_PROXY_HEADERS:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # "client, proxy1, proxy2" -> "client"
            return forwarded.split(",")[0].strip()

    if request.client is None:
        return None

    return request.client.host
