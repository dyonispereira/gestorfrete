from __future__ import annotations

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """One field-level validation failure (``docs/api/ERROR_MODEL.md``,
    "Erro de validação — formato de details")."""

    field: str
    code: str
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] = []
    request_id: str | None = None
    correlation_id: str | None = None


class ErrorEnvelope(BaseModel):
    """The single error shape every endpoint in the frozen OpenAPI contract
    returns (``docs/api/ERROR_MODEL.md`` §"Envelope único") — one Pydantic
    model shared by every exception handler so the JSON shape can never
    drift between error categories.
    """

    error: ErrorBody
