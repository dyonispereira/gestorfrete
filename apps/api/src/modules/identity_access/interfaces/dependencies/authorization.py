from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Depends

from core.database.session import get_session_factory
from interfaces.dependencies.auth import get_current_actor
from modules.identity_access.application.authorization_service import AuthorizationService
from shared_kernel.domain.actor import AuthenticatedActor


def get_authorization_service() -> AuthorizationService:
    return AuthorizationService(get_session_factory())


def require_permission(
    code: str,
) -> Callable[..., Coroutine[Any, Any, AuthenticatedActor]]:
    """Dependency factory usada por todo router protegido de qualquer bounded context — não só
    `identity_access` (`AUTHORIZATION_IMPLEMENTATION.md`). Encadeia com `get_current_actor`
    (Foundation, Lote 1) — nunca duplica a resolução de JWT/tenant/sessão, só adiciona a checagem
    de RBAC sobre o Actor já resolvido.
    """

    async def _dependency(
        actor: AuthenticatedActor = Depends(get_current_actor),
        authz: AuthorizationService = Depends(get_authorization_service),
    ) -> AuthenticatedActor:
        await authz.authorize(actor, code)
        return actor

    return _dependency
