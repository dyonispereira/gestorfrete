from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError
from modules.documents.application.dtos.mdfe_dto import MdfeDTO
from modules.documents.domain.entities.mdfe_status_history_entry import MdfeStatusHistoryEntry
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_mdfe_repository import (
    SqlAlchemyMdfeRepository,
)
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_mdfe_status_history_repository import (
    SqlAlchemyMdfeStatusHistoryRepository,
)
from modules.freight.application.trip_internal_transitions import TripInternalTransitions
from modules.freight.domain.value_objects.trip_fiscal_status import TripFiscalStatus
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_delivery_repository import (
    SqlAlchemyDeliveryRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CloseMdfeCommand(Command):
    actor: AuthenticatedActor
    mdfe_id: uuid.UUID


class CloseMdfeHandler(CommandHandler[CloseMdfeCommand, MdfeDTO]):
    """`AUTORIZADO→ENCERRADO`. Precondição real: nenhuma Entrega pendente na Viagem
    (`DeliveryRepository.count_pending_for_trip`, D356-style leitura cross-module). `040-mdfe.md`
    descreve isso como "normalmente derivado automaticamente" por um consumidor de
    `EntregaRealizada" — este backend não liga esse gatilho a nenhum handler de `freight` (D375);
    este comando é o único caminho reachável via HTTP até `ENCERRADO`, exatamente como
    `documents.mdfe.close` já prevê para confirmação manual."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CloseMdfeCommand) -> MdfeDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            mdfe_repo = SqlAlchemyMdfeRepository(uow.session)
            history_repo = SqlAlchemyMdfeStatusHistoryRepository(uow.session)
            delivery_repo = SqlAlchemyDeliveryRepository(uow.session)

            mdfe = await mdfe_repo.get_by_id(command.mdfe_id)
            if mdfe is None:
                raise NotFoundError("FISCAL_MDFE_NOT_FOUND", "MDF-e não encontrado.")

            pending = await delivery_repo.count_pending_for_trip(mdfe.viagem_id)
            if pending > 0:
                raise ConflictError(
                    "FISCAL_MDFE_LAST_DELIVERY_PENDING", "Ainda há Entregas pendentes na Viagem."
                )

            now = datetime.now(timezone.utc)
            mdfe.close(now=now)
            await mdfe_repo.add(mdfe)
            cte_ids = await mdfe_repo.list_cte_ids(mdfe.id)

            await history_repo.add(
                MdfeStatusHistoryEntry.create(
                    mdfe_id=mdfe.id, status=mdfe.status.value, usuario_id=command.actor.user_id,
                    origem="usuario", now=now,
                )
            )
            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="mdfes", entidade_id=mdfe.id,
                acao="TRANSICAO_STATUS", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"status": mdfe.status.value},
            )
            await uow.commit()

        await TripInternalTransitions().record_fiscal_transition(
            trip_id=mdfe.viagem_id, status=TripFiscalStatus.MDFE_ENCERRADO, now=now
        )

        return MdfeDTO.from_entity(mdfe, cte_ids=cte_ids)
