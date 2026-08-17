from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError
from modules.reporting.application.dtos.saved_filter_dto import SavedFilterDTO
from modules.reporting.domain.entities.saved_filter import SavedFilter
from modules.reporting.infrastructure.persistence.repositories.sqlalchemy_saved_filter_repository import (
    SqlAlchemySavedFilterRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateSavedFilterCommand(Command):
    actor: AuthenticatedActor
    name: str
    criteria: dict[str, Any]


class CreateSavedFilterHandler(CommandHandler[CreateSavedFilterCommand, SavedFilterDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateSavedFilterCommand) -> SavedFilterDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemySavedFilterRepository(uow.session)
            if await repo.exists_with_name(command.actor.user_id, command.name):
                raise ConflictError("REPORTING_SAVED_FILTER_NAME_ALREADY_EXISTS", "Já existe um Filtro com esse nome.")

            saved_filter = SavedFilter.create(usuario_id=command.actor.user_id, nome=command.name, criterios=command.criteria)
            await repo.add(saved_filter)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="filtros_favoritos",
                entidade_id=saved_filter.id, acao="CRIACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id), dados_depois={"name": command.name},
            )
            await uow.commit()

        return SavedFilterDTO.from_entity(saved_filter)
