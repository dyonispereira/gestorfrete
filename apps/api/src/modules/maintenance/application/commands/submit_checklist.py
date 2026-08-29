from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.maintenance.application.dtos.checklist_dto import ChecklistDTO
from modules.maintenance.domain.entities.checklist_status_history_entry import ChecklistStatusHistoryEntry
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_checklist_repository import (
    SqlAlchemyChecklistRepository,
)
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_checklist_status_history_repository import (
    SqlAlchemyChecklistStatusHistoryRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class SubmitChecklistCommand(Command):
    actor: AuthenticatedActor
    checklist_id: uuid.UUID
    itens: list[dict[str, Any]]


class SubmitChecklistHandler(CommandHandler[SubmitChecklistCommand, ChecklistDTO]):
    """`EM_PREENCHIMENTO→CONCLUIDO` — exige todo item respondido (`Checklist.submit`)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: SubmitChecklistCommand) -> ChecklistDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            checklist_repo = SqlAlchemyChecklistRepository(uow.session)
            history_repo = SqlAlchemyChecklistStatusHistoryRepository(uow.session)

            checklist = await checklist_repo.get_by_id(command.checklist_id)
            if checklist is None:
                raise NotFoundError("MAINTENANCE_CHECKLIST_NOT_FOUND", "Checklist não encontrado.")

            now = datetime.now(timezone.utc)
            checklist.submit(itens=command.itens, now=now)
            await checklist_repo.add(checklist)
            await history_repo.add(
                ChecklistStatusHistoryEntry.create(
                    checklist_id=checklist.id, status=checklist.status.value, usuario_id=command.actor.user_id,
                    origem="usuario", now=now,
                )
            )
            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="checklists", entidade_id=checklist.id,
                acao="TRANSICAO_STATUS", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"status": checklist.status.value, "itens": checklist.itens},
            )
            await uow.commit()

        return ChecklistDTO.from_entity(checklist)
