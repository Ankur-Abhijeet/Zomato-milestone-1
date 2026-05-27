"""Request-ID middleware (Phase 6).

Injects a unique X-Request-ID on every response.
Reads from the inbound header first (trust upstream proxy / load balancer),
falls back to a new uuid4 if absent.

Also logs method, path, status, and duration_ms on every response so
structured log aggregators (Datadog, CloudWatch) can build latency metrics.
"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a request ID to every request/response cycle."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        # Honour upstream proxy header; generate fresh UUID if absent
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id

        start = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 1)

        response.headers[REQUEST_ID_HEADER] = request_id

        logger.info(
            "%s %s %s %.1fms [%s]",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )

        return response
