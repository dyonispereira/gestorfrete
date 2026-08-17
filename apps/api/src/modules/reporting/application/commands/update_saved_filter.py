from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import AuthorizationError, NotFoundError
from modules.reporting.application.dtos.saved_filter_dto import SavedFilterDTO
from modules.reporting.infrastructure.persistence.repositories.sqlalchemy_saved_filter_repository import (
    SqlAlchemySavedFilterRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateSavedFilterCommand(Command):
    actor: AuthenticatedActor
    saved_filter_id: uuid.UUID
    name: str | None
    criteria: dict[str, Any] | None
    status: str | None


class UpdateSavedFilterHandler(CommandHandler[UpdateSavedFilterCommand, SavedFilterDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: UpdateSavedFilterCommand) -> SavedFilterDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemySavedFilterRepository(uow.session)
            saved_filter = await repo.get_by_id(command.saved_filter_id)
            if saved_filter is None:
                raise NotFoundError("REPORTING_SAVED_FILTER_NOT_FOUND", "Filtro Favorito não encontrado.")
            if saved_filter.usuario_id != command.actor.user_id:
                raise AuthorizationError("REPORTING_SAVED_FILTER_NOT_OWNED", "Só o dono edita o Filtro Favorito.")

            saved_filter.update(nome=command.name, criterios=command.criteria, status=command.status)
            await repo.add(saved_filter)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="filtros_favoritos",
                entidade_id=saved_filter.id, acao="ALTERACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )
            await uow.commit()

        return SavedFilterDTO.from_entity(saved_filter)
