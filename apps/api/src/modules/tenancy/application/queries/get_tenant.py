from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import InfrastructureError
from modules.tenancy.application.dtos.tenant_dto import TenantDTO
from modules.tenancy.infrastructure.persistence.repositories.sqlalchemy_tenant_repository import (
    SqlAlchemyTenantRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetTenantQuery(Query):
    actor: AuthenticatedActor


class GetTenantHandler(QueryHandler[GetTenantQuery, TenantDTO]):
    """Queries são leitura pura — abrem sua própria sessão (`APPLICATION_LAYER.md`: "QueryHandler
    pode ler direto da infraestrutura, sem o peso de um UnitOfWork de escrita"), nunca compartilham
    transação com um Command."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetTenantQuery) -> TenantDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyTenantRepository(session)
            # D338/D339 — nunca outro id além do tenant já resolvido no Actor Context.
            tenant = await repo.get_by_id(query.actor.tenant_id)
        if tenant is None:
            raise InfrastructureError(
                "TENANCY_CONTEXT_TENANT_MISSING",
                "O tenant do contexto autenticado não foi encontrado.",
            )
        return TenantDTO.from_entity(tenant)
