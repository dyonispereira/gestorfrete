from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import AuthorizationError, NotFoundError
from modules.reporting.infrastructure.persistence.repositories.sqlalchemy_saved_filter_repository import (
    SqlAlchemySavedFilterRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class DeleteSavedFilterCommand(Command):
    actor: AuthenticatedActor
    saved_filter_id: uuid.UUID


class DeleteSavedFilterHandler(CommandHandler[DeleteSavedFilterCommand, None]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: DeleteSavedFilterCommand) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemySavedFilterRepository(uow.session)
            saved_filter = await repo.get_by_id(command.saved_filter_id)
            if saved_filter is None:
                raise NotFoundError("REPORTING_SAVED_FILTER_NOT_FOUND", "Filtro Favorito não encontrado.")
            if saved_filter.usuario_id != command.actor.user_id:
                raise AuthorizationError("REPORTING_SAVED_FILTER_NOT_OWNED", "Só o dono exclui o Filtro Favorito.")

            saved_filter.archive()
            await repo.add(saved_filter)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="filtros_favoritos",
                entidade_id=saved_filter.id, acao="EXCLUSAO_LOGICA", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )
            await uow.commit()
