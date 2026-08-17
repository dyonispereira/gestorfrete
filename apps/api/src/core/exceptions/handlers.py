from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from core.exceptions.base import ApplicationError
from core.exceptions.envelope import ErrorBody, ErrorDetail, ErrorEnvelope
from core.observability.context import get_correlation_id, get_request_id

logger = logging.getLogger(__name__)


def _envelope(code: str, message: str, details: list[ErrorDetail] | None = None) -> dict[str, Any]:
    body = ErrorEnvelope(
        error=ErrorBody(
            code=code,
            message=message,
            details=details or [],
            request_id=get_request_id(),
            correlation_id=get_correlation_id(),
        )
    )
    return body.model_dump(mode="json")


async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
    if exc.http_status >= 500:
        logger.error(
            "application_error",
            extra={"error_code": exc.code, "http_status": exc.http_status, "path": request.url.path},
            exc_info=exc,
        )
    else:
        logger.info(
            "application_error",
            extra={"error_code": exc.code, "http_status": exc.http_status, "path": request.url.path},
        )
    details = [ErrorDetail(**d) if not isinstance(d, ErrorDetail) else d for d in exc.details]
    return JSONResponse(status_code=exc.http_status, content=_envelope(exc.code, exc.message, details))


async def request_validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Maps Pydantic/FastAPI's own payload validation failures to the same
    envelope, ``VALIDATION_FAILED`` (ERROR_MODEL.md) — the Controller never
    writes this translation by hand (D214)."""

    details = [
        ErrorDetail(
            field=".".join(str(p) for p in err["loc"] if p != "body"),
            code=err["type"].upper(),
            message=err["msg"],
        )
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=_envelope("VALIDATION_FAILED", "Um ou mais campos são inválidos.", details),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for anything not raised as an ``ApplicationError`` — logs
    the full exception server-side (correlated by ``request_id``) and
    returns the generic envelope, **never** the exception message or a stack
    trace to the client, in any environment (ERROR_MODEL.md, explicit rule).
    """

    logger.error("unhandled_exception", extra={"path": request.url.path}, exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_envelope("INTERNAL_SERVER_ERROR", "Erro interno do servidor."),
    )


def register_exception_handlers(app: FastAPI) -> None:
    # Starlette's `add_exception_handler` stub types the handler as
    # `Callable[[Request, Exception], ...]` regardless of which exception
    # class is registered — narrowing the parameter type on each concrete
    # handler above is intentional (so mypy still checks their bodies
    # against the right attributes, e.g. `exc.code`) and is FastAPI's own
    # documented pattern; the mismatch is a stub limitation, not a real
    # type error, so it is silenced here rather than widened everywhere.
    app.add_exception_handler(ApplicationError, application_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)
