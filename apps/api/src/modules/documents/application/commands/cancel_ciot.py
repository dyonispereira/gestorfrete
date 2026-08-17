from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError, ValidationError
from modules.documents.application.dtos.ciot_dto import CiotDTO
from modules.documents.domain.entities.ciot_status_history_entry import CiotStatusHistoryEntry
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_ciot_repository import (
    SqlAlchemyCiotRepository,
)
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_ciot_status_history_repository import (
    SqlAlchemyCiotStatusHistoryRepository,
)
from modules.freight.domain.value_objects.trip_operational_status import TripOperationalStatus
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor

_STATUSES_ANTES_DO_INICIO = frozenset(
    {
        TripOperationalStatus.RASCUNHO, TripOperationalStatus.PLANEJADA,
        TripOperationalStatus.AGUARDANDO_CHECKLIST, TripOperationalStatus.LIBERADA,
    }
)


@dataclass(frozen=True)
class CancelCiotCommand(Command):
    actor: AuthenticatedActor
    ciot_id: uuid.UUID
    notes: str


class CancelCiotHandler(CommandHandler[CancelCiotCommand, CiotDTO]):
    """`PENDENTE`/`REGISTRADO→CANCELADO`, só antes de `Trip.status_operacional` avançar para
    `EM_DESLOCAMENTO` ou posterior."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CancelCiotCommand) -> CiotDTO:
        if not command.notes or not command.notes.strip():
            raise ValidationError("FISCAL_CIOT_NOTES_REQUIRED", "notes é obrigatória para cancelar.")

        async with SQLAlchemyUnitOfWork() as uow:
            ciot_repo = SqlAlchemyCiotRepository(uow.session)
            history_repo = SqlAlchemyCiotStatusHistoryRepository(uow.session)
            trip_repo = SqlAlchemyTripRepository(uow.session)

            ciot = await ciot_repo.get_by_id(command.ciot_id)
            if ciot is None:
                raise NotFoundError("FISCAL_CIOT_NOT_FOUND", "CIOT não encontrado.")

            trip = await trip_repo.get_by_id(ciot.viagem_id)
            if trip is not None and trip.status_operacional not in _STATUSES_ANTES_DO_INICIO:
                raise ConflictError(
                    "FISCAL_CIOT_TRIP_ALREADY_STARTED", "A Viagem já iniciou o deslocamento."
                )

            now = datetime.now(timezone.utc)
            ciot.cancel()
            await ciot_repo.add(ciot)

            await history_repo.add(
                CiotStatusHistoryEntry.create(
                    ciot_id=ciot.id, status=ciot.status.value, usuario_id=command.actor.user_id,
                    origem="usuario", now=now, observacao=command.notes,
                )
            )
            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="ciots", entidade_id=ciot.id,
                acao="TRANSICAO_STATUS", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"status": ciot.status.value}, motivo=command.notes,
            )
            await uow.commit()

        return CiotDTO.from_entity(ciot)
