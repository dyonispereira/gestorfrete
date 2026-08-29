from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.freight.application.trip_internal_transitions import TripInternalTransitions
from modules.maintenance.application.dtos.checklist_dto import ChecklistDTO
from modules.maintenance.domain.entities.checklist_status_history_entry import ChecklistStatusHistoryEntry
from modules.maintenance.domain.value_objects.checklist_referencia_tipo import ChecklistReferenciaTipo
from modules.maintenance.domain.value_objects.checklist_type import ChecklistType
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_checklist_repository import (
    SqlAlchemyChecklistRepository,
)
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_checklist_status_history_repository import (
    SqlAlchemyChecklistStatusHistoryRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ApproveChecklistCommand(Command):
    actor: AuthenticatedActor
    checklist_id: uuid.UUID


class ApproveChecklistHandler(CommandHandler[ApproveChecklistCommand, ChecklistDTO]):
    """`CONCLUIDO→APROVADO`. Quando `TIPO=MOTORISTA_SAIDA` e `REFERENCIA_TIPO=VIAGEM`, é este
    comando que fecha o gap identificado nas Lotes Operação/Documentos Fiscais: chama
    `TripInternalTransitions.approve_checklist` (já existente em `freight`, D376), completando
    `AGUARDANDO_CHECKLIST→LIBERADA` de verdade — sem nenhuma alteração em `freight`."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: ApproveChecklistCommand) -> ChecklistDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            checklist_repo = SqlAlchemyChecklistRepository(uow.session)
            history_repo = SqlAlchemyChecklistStatusHistoryRepository(uow.session)

            checklist = await checklist_repo.get_by_id(command.checklist_id)
            if checklist is None:
                raise NotFoundError("MAINTENANCE_CHECKLIST_NOT_FOUND", "Checklist não encontrado.")

            now = datetime.now(timezone.utc)
            checklist.approve(now=now)
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
                dados_depois={"status": checklist.status.value},
            )
            await uow.commit()

        if checklist.tipo is ChecklistType.MOTORISTA_SAIDA and checklist.referencia_tipo is ChecklistReferenciaTipo.VIAGEM:
            await TripInternalTransitions().approve_checklist(
                trip_id=checklist.referencia_id, now=datetime.now(timezone.utc)
            )

        return ChecklistDTO.from_entity(checklist)
