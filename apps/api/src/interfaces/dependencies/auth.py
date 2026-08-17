from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.config.settings import Settings, get_settings
from core.exceptions.base import AuthenticationError
from core.multitenancy.context import reset_current_tenant_id, set_current_tenant_id
from core.security.jwt_token_service import InvalidTokenError, JWTTokenService, TokenExpiredError
from core.security.session_validation import SessionValidator, get_session_validator
from shared_kernel.domain.actor import AuthenticatedActor

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_actor(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    settings: Settings = Depends(get_settings),
    session_validator: SessionValidator = Depends(get_session_validator),
) -> AsyncGenerator[AuthenticatedActor, None]:
    """Resolves the ``AuthenticatedActor`` for the current request and puts
    its tenant in scope for the whole request lifetime (D208/D212 —
    ``AUTHENTICATION.md``'s pipeline: Autenticação → Tenant → RBAC → Ação).

    Every protected router depends on this — never on a raw ``tenant_id``
    parameter — so no repository or handler in any module ever needs a
    tenant passed in manually (``shared_kernel.domain.repository``).

    RBAC itself (checking a specific permission code) is a separate,
    per-endpoint dependency added when the first real endpoint is built in
    Sprint 11 Lote 2 — this foundation only proves identity and tenant, it
    does not yet know about ``RBAC_MATRIX.md``.
    """

    if credentials is None:
        raise AuthenticationError("IDENTITY_MISSING_CREDENTIALS", "Token de acesso ausente.")

    token_service = JWTTokenService(settings)
    try:
        claims = token_service.decode_access_token(credentials.credentials)
    except TokenExpiredError as exc:
        raise AuthenticationError("IDENTITY_TOKEN_EXPIRED", "Token de acesso expirado.") from exc
    except InvalidTokenError as exc:
        raise AuthenticationError("IDENTITY_INVALID_CREDENTIALS", "Token de acesso inválido.") from exc

    try:
        user_id = uuid.UUID(str(claims["sub"]))
        tenant_id = uuid.UUID(str(claims["tenant_id"]))
        session_id = uuid.UUID(str(claims["session_id"]))
    except (KeyError, ValueError) as exc:
        raise AuthenticationError(
            "IDENTITY_INVALID_CREDENTIALS", "Token de acesso não contém identidade/tenant/sessão válidos."
        ) from exc

    if not await session_validator.is_session_valid(session_id):
        raise AuthenticationError(
            "IDENTITY_SESSION_REVOKED", "Sessão encerrada, expirada ou inexistente."
        )

    token = set_current_tenant_id(tenant_id)
    try:
        yield AuthenticatedActor(user_id=user_id, tenant_id=tenant_id, session_id=session_id)
    finally:
        reset_current_tenant_id(token)
