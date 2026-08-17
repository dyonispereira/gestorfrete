from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from core.observability.context import (
    CORRELATION_ID_HEADER,
    REQUEST_ID_HEADER,
    new_request_id,
    set_correlation_id,
    set_request_id,
)

logger = logging.getLogger("http.access")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """First middleware in the chain (registered last in ``main.py`` so it
    runs outermost) — establishes ``request_id``/``correlation_id`` for
    everything downstream (exception handlers, structured logs,
    ``ErrorEnvelope``) and emits one structured access-log line per request
    with method/path/status/duration (``docs/backend/OBSERVABILITY.md``).

    Never logs the request/response body — payloads can contain sensitive
    fields (CPF, tokens); only metadata about the call is recorded here.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or new_request_id()
        correlation_id = request.headers.get(CORRELATION_ID_HEADER) or request_id

        set_request_id(request_id)
        set_correlation_id(correlation_id)

        started_at = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            logger.error(
                "request_failed",
                extra={
                    "http_method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                },
                exc_info=True,
            )
            raise

        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.info(
            "request_completed",
            extra={
                "http_method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        response.headers[REQUEST_ID_HEADER] = request_id
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        return response
