from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class AuthenticatedActor:
    """Who is making the current request — resolved once per request from
    the access token (``AUTHENTICATION.md``) and threaded through
    Application/Interfaces without ever being re-derived from client input.

    ``tenant_id`` is never optional here: by the time an ``AuthenticatedActor``
    exists, the tenant has already been resolved from the token (D208) — a
    request with no valid tenant claim never reaches this type, it fails
    authentication first.

    ``session_id`` (Sprint 11 Lote 2) identifies the ``Session`` (``sessoes_acesso``)
    that produced this token — ``get_current_actor`` validates it is still
    ``ATIVA`` before this type is ever constructed, which is what makes
    session revocation take effect immediately instead of waiting for the
    access token to expire on its own.
    """

    user_id: uuid.UUID
    tenant_id: uuid.UUID
    session_id: uuid.UUID
