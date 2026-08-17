from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from modules.identity_access.domain.entities.session import Session
from modules.identity_access.domain.repositories.session_repository import SessionRepository
from modules.identity_access.domain.value_objects.enums import SessionEndedReason, SessionStatus
from modules.identity_access.infrastructure.persistence.models.identity_models import (
    SessionModel,
    UserModel,
)
from shared_kernel.domain.specification import Specification


def _to_entity(model: SessionModel) -> Session:
    return Session(
        id=model.id,
        user_id=model.usuario_id,
        started_at=model.data_hora_inicio,
        expires_at=model.data_hora_expiracao_prevista,
        ended_reason=SessionEndedReason(model.motivo_encerramento) if model.motivo_encerramento else None,
        status=SessionStatus(model.status),
    )


class SqlAlchemySessionRepository(SessionRepository):
    """`get_by_id` **não** filtra por tenant — resolver uma Sessão a partir do `session_id` de um
    JWT precisa funcionar antes de `set_current_tenant_id` acontecer
    (`interfaces.dependencies.auth.get_current_actor` valida a sessão *antes* de montar o
    `AuthenticatedActor`, `SESSION_IMPLEMENTATION.md`)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Session | None:
        model = await self._session.get(SessionModel, id)
        return _to_entity(model) if model is not None else None

    async def add(self, aggregate: Session) -> None:
        model = await self._session.get(SessionModel, aggregate.id)
        if model is None:
            # Sessão não carrega `tenant_id` próprio no Domain (é sempre o tenant do Usuário dono,
            # nunca um dado independente) — resolvido aqui, não via `core.multitenancy.context`,
            # porque a criação de Sessão (login) acontece *antes* de qualquer contexto de tenant
            # existir (D208's exceção documentada, mesma de `UserRepository.get_by_email`).
            tenant_id = (
                await self._session.execute(
                    select(UserModel.tenant_id).where(UserModel.id == aggregate.user_id)
                )
            ).scalar_one()
            model = SessionModel(
                id=aggregate.id, tenant_id=tenant_id, usuario_id=aggregate.user_id
            )
            self._session.add(model)
        model.data_hora_inicio = aggregate.started_at
        model.data_hora_expiracao_prevista = aggregate.expires_at
        model.motivo_encerramento = aggregate.ended_reason.value if aggregate.ended_reason else None
        model.status = aggregate.status.value

    async def end_all_active_for_user(self, user_id: uuid.UUID, reason: SessionEndedReason) -> None:
        stmt = (
            update(SessionModel)
            .where(SessionModel.usuario_id == user_id, SessionModel.status == SessionStatus.ATIVA.value)
            .values(status=SessionStatus.ENCERRADA.value, motivo_encerramento=reason.value)
        )
        await self._session.execute(stmt)

    async def find(self, specification: Specification[Session]) -> list[Session]:
        raise NotImplementedError("Sem endpoint de listagem de Sessão neste lote")
