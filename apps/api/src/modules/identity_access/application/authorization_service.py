from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import AuthorizationError
from modules.identity_access.infrastructure.persistence.models.identity_models import (
    PermissionModel,
    papel_permissao,
    usuarios_papeis,
)
from shared_kernel.domain.actor import AuthenticatedActor


class AuthorizationService:
    """D340 — RBAC sempre resolvido ao vivo a partir de `usuarios_papeis`/`papel_permissao`/
    `permissoes`, nunca de um claim do JWT. Uma instância nova por requisição
    (`get_authorization_service`, escopada pelo FastAPI) — o resultado nunca é cacheado entre
    requisições (`AUTHORIZATION_IMPLEMENTATION.md`)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_permission_codes(self, actor: AuthenticatedActor) -> frozenset[str]:
        stmt = (
            select(PermissionModel.codigo)
            .distinct()
            .select_from(usuarios_papeis)
            .join(papel_permissao, papel_permissao.c.papel_id == usuarios_papeis.c.papel_id)
            .join(PermissionModel, PermissionModel.id == papel_permissao.c.permissao_id)
            .where(usuarios_papeis.c.usuario_id == actor.user_id)
        )
        async with self._session_factory() as session:
            rows = (await session.execute(stmt)).scalars().all()
        return frozenset(rows)

    async def authorize(self, actor: AuthenticatedActor, permission_code: str) -> None:
        codes = await self.get_permission_codes(actor)
        if permission_code not in codes:
            raise AuthorizationError(
                "IDENTITY_PERMISSION_DENIED",
                f"Ação requer a permissão '{permission_code}'.",
            )
