"""
CyberRisk360

Purpose:
Set standard security-related response headers on every response.
"""

from starlette.middleware.base import BaseHTTPMiddleware

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    # Inert over plain HTTP; browsers only honor this over TLS, so
    # it's safe to always send.
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
    # This API never serves HTML/JS, so a maximally restrictive CSP
    # is safe and cheap.
    "Content-Security-Policy": "default-src 'none'"
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):

        response = await call_next(request)

        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value

        return response
