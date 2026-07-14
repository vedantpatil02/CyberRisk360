"""
CyberRisk360

Purpose:
Per-request logging and correlation. Assigns/propagates a request id
(echoed as the `X-Request-ID` response header) and logs each request's
method, path, status, timing, and client IP as one structured record.
"""

import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger
from app.core.net import get_client_ip


logger = get_logger("request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):

        # Reuse an inbound request id (from a proxy/gateway) if present,
        # otherwise mint one, so logs can be correlated end-to-end.
        request_id = (
            request.headers.get("x-request-id") or uuid4().hex
        )

        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client_ip": get_client_ip(request),
            },
        )

        return response
