from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import InfrastructureError
from modules.identity_access.application.dtos.auth_dto import MeResultDTO, SessionDTO
from modules.identity_access.application.dtos.user_dto import UserDTO
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_role_repository import (
    SqlAlchemyRoleRepository,
)
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_session_repository import (
    SqlAlchemySessionRepository,
)
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from modules.tenancy.application.dtos.tenant_dto import TenantDTO
from modules.tenancy.infrastructure.persistence.repositories.sqlalchemy_tenant_repository import (
    SqlAlchemyTenantRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetMeQuery(Query):
    actor: AuthenticatedActor


class GetMeHandler(QueryHandler[GetMeQuery, MeResultDTO]):
    """`user.roles` vem expandido (nomes, não IDs) — `001-authentication.md`: "é a própria
    identidade do ator, o Frontend precisa disso imediatamente após login"."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetMeQuery) -> MeResultDTO:
        async with self._session_factory() as session:
            user_repo = SqlAlchemyUserRepository(session)
            role_repo = SqlAlchemyRoleRepository(session)
            tenant_repo = SqlAlchemyTenantRepository(session)
            session_repo = SqlAlchemySessionRepository(session)

            user = await user_repo.get_by_id(query.actor.user_id)
            if user is None:
                raise InfrastructureError("IDENTITY_ACTOR_USER_MISSING", "Usuário do contexto autenticado não encontrado.")

            tenant = await tenant_repo.get_by_id(query.actor.tenant_id)
            if tenant is None:
                raise InfrastructureError("TENANCY_CONTEXT_TENANT_MISSING", "Tenant do contexto autenticado não encontrado.")

            access_session = await session_repo.get_by_id(query.actor.session_id)
            if access_session is None:
                raise InfrastructureError("IDENTITY_ACTOR_SESSION_MISSING", "Sessão do contexto autenticado não encontrada.")

            roles = await role_repo.get_many(user.role_ids)

        return MeResultDTO(
            user=UserDTO.from_entity(user),
            tenant=TenantDTO.from_entity(tenant),
            session=SessionDTO(
                id=str(access_session.id),
                started_at=access_session.started_at.isoformat(),
                expires_at=access_session.expires_at.isoformat(),
                status=access_session.status.value,
            ),
            role_names=sorted(r.nome for r in roles),
        )
