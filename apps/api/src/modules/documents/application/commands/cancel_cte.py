from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError, ValidationError
from modules.documents.application.dtos.cte_dto import CteDTO
from modules.documents.domain.entities.cte_status_history_entry import CteStatusHistoryEntry
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_cte_repository import (
    SqlAlchemyCteRepository,
)
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_cte_status_history_repository import (
    SqlAlchemyCteStatusHistoryRepository,
)
from modules.freight.application.trip_internal_transitions import TripInternalTransitions
from modules.freight.domain.value_objects.trip_fiscal_status import TripFiscalStatus
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CancelCteCommand(Command):
    actor: AuthenticatedActor
    cte_id: uuid.UUID
    notes: str


class CancelCteHandler(CommandHandler[CancelCteCommand, CteDTO]):
    """`AUTORIZADO→CANCELADO`. D398 — avança `Trip.status_fiscal` para `CTE_CANCELADO`."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CancelCteCommand) -> CteDTO:
        if not command.notes or not command.notes.strip():
            raise ValidationError("FISCAL_CTE_NOTES_REQUIRED", "notes é obrigatória para cancelar.")

        async with SQLAlchemyUnitOfWork() as uow:
            cte_repo = SqlAlchemyCteRepository(uow.session)
            history_repo = SqlAlchemyCteStatusHistoryRepository(uow.session)

            cte = await cte_repo.get_by_id(command.cte_id)
            if cte is None:
                raise NotFoundError("FISCAL_CTE_NOT_FOUND", "CT-e não encontrado.")

            now = datetime.now(timezone.utc)
            cte.cancel(now=now)
            await cte_repo.add(cte)

            await history_repo.add(
                CteStatusHistoryEntry.create(
                    cte_id=cte.id, status=cte.status.value, usuario_id=command.actor.user_id,
                    origem="usuario", now=now, observacao=command.notes,
                )
            )
            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="ctes", entidade_id=cte.id,
                acao="TRANSICAO_STATUS", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"status": cte.status.value}, motivo=command.notes,
            )
            await uow.commit()

        await TripInternalTransitions().record_fiscal_transition(
            trip_id=cte.viagem_id, status=TripFiscalStatus.CTE_CANCELADO, now=datetime.now(timezone.utc)
        )

        return CteDTO.from_entity(cte)
