"""
CyberRisk360

Purpose:
Set standard security-related response headers on every response.

The Content-Security-Policy is chosen per response:

  * JSON API responses get a maximally restrictive `default-src 'none'`.
  * The interactive docs (`/docs`, `/redoc`) load Swagger UI / ReDoc
    assets from a CDN and run an inline bootstrap script, so they get a
    docs-specific policy - otherwise the page renders blank.
  * HTML responses (the `/reports/*?format=html` views) use only inline
    `<style>` and embedded/`data:` images, so they get a policy that
    allows exactly that and nothing else.
"""

from starlette.middleware.base import BaseHTTPMiddleware


# Applied to everything that isn't HTML - the API's normal surface.
STRICT_CSP = "default-src 'none'"

# Swagger UI and ReDoc pull CSS/JS from jsdelivr, initialise via an
# inline script, and (Swagger) fetch /openapi.json from same origin.
DOCS_CSP = (
    "default-src 'none'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' data: https://fastapi.tiangolo.com; "
    "font-src 'self' https://cdn.jsdelivr.net; "
    "connect-src 'self'"
)

# Rendered HTML reports: inline styles + inline/data: images only. No
# scripts, no external origins.
HTML_CSP = (
    "default-src 'none'; "
    "style-src 'unsafe-inline'; "
    "img-src 'self' data:"
)

DOCS_PATHS = ("/docs", "/redoc")

STATIC_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    # Inert over plain HTTP; browsers only honor this over TLS, so
    # it's safe to always send.
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
}


def _content_security_policy(request, response):
    """
    Pick the CSP that matches what this response actually serves.
    """

    if request.url.path in DOCS_PATHS:
        return DOCS_CSP

    content_type = response.headers.get("content-type", "")

    if content_type.startswith("text/html"):
        return HTML_CSP

    return STRICT_CSP


class SecurityHeadersMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):

        response = await call_next(request)

        for header, value in STATIC_SECURITY_HEADERS.items():
            response.headers[header] = value

        response.headers["Content-Security-Policy"] = (
            _content_security_policy(request, response)
        )

        return response
