from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError, ValidationError
from modules.maintenance.application.dtos.checklist_dto import ChecklistDTO
from modules.maintenance.domain.entities.checklist import Checklist
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
class RejectChecklistCommand(Command):
    actor: AuthenticatedActor
    checklist_id: uuid.UUID
    observacao: str


class RejectChecklistHandler(CommandHandler[RejectChecklistCommand, ChecklistDTO]):
    """`CONCLUIDO→REPROVADO`. Um Checklist `Reprovado` nunca é reaberto — este comando sempre cria
    um novo Checklist `Pendente` (mesmo tipo/referência/veículo/motorista), referenciando o
    reprovado (`007-CHECKLIST.md`). Quando a referência é uma Viagem, ela permanece em
    `AGUARDANDO_CHECKLIST` (nunca recua nem avança sozinha) — nenhuma chamada a `freight` é
    necessária aqui, diferente de `approve_checklist`."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: RejectChecklistCommand) -> ChecklistDTO:
        if not command.observacao or not command.observacao.strip():
            raise ValidationError(
                "MAINTENANCE_CHECKLIST_OBSERVACAO_REQUIRED", "observacao é obrigatória para reprovar."
            )

        async with SQLAlchemyUnitOfWork() as uow:
            checklist_repo = SqlAlchemyChecklistRepository(uow.session)
            history_repo = SqlAlchemyChecklistStatusHistoryRepository(uow.session)

            checklist = await checklist_repo.get_by_id(command.checklist_id)
            if checklist is None:
                raise NotFoundError("MAINTENANCE_CHECKLIST_NOT_FOUND", "Checklist não encontrado.")

            now = datetime.now(timezone.utc)
            checklist.reject(now=now)
            await checklist_repo.add(checklist)
            await history_repo.add(
                ChecklistStatusHistoryEntry.create(
                    checklist_id=checklist.id, status=checklist.status.value, usuario_id=command.actor.user_id,
                    origem="usuario", now=now, observacao=command.observacao,
                )
            )

            novo_checklist = Checklist.create(
                tipo=checklist.tipo, referencia_tipo=checklist.referencia_tipo, referencia_id=checklist.referencia_id,
                veiculo_tracionador_id=checklist.veiculo_tracionador_id, motorista_id=checklist.motorista_id,
                now=now, checklist_reprovado_id=checklist.id,
            )
            await checklist_repo.add(novo_checklist)
            await history_repo.add(
                ChecklistStatusHistoryEntry.create(
                    checklist_id=novo_checklist.id, status=novo_checklist.status.value, usuario_id=None,
                    origem="sistema", now=now,
                    observacao=f"Criado automaticamente após reprovação do Checklist {checklist.codigo}.",
                )
            )

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="checklists", entidade_id=checklist.id,
                acao="TRANSICAO_STATUS", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"status": checklist.status.value, "novo_checklist_id": str(novo_checklist.id)},
                motivo=command.observacao,
            )
            await uow.commit()

        return ChecklistDTO.from_entity(checklist)
