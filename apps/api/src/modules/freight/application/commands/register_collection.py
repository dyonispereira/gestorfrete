from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError
from modules.freight.application.dtos.collection_dto import CollectionDTO
from modules.freight.domain.entities.collection import Collection
from modules.freight.domain.entities.trip_status_history_entry import TripStatusHistoryEntry
from modules.freight.domain.value_objects.status_history_dimension import StatusHistoryDimension
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_collection_repository import (
    SqlAlchemyCollectionRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_status_history_repository import (
    SqlAlchemyTripStatusHistoryRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class RegisterCollectionCommand(Command):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    conferencia_ok: bool


class RegisterCollectionHandler(CommandHandler[RegisterCollectionCommand, CollectionDTO]):
    """`POST /viagens/{id}/coletas` — V1 Operational Hardening, Parte 2. Fecha
    `EM_DESLOCAMENTO → CARREGANDO` (`018-trip-status.md`), a primeira das duas transições que até
    aqui só existiam simuladas em teste (`TripInternalTransitions.register_collection`). Usa
    exatamente `Trip.mark_collected()`, o mesmo método de domínio já formalizado — nenhuma regra
    nova, nenhuma duplicada. Uma Viagem só tem uma Coleta neste V1 (múltiplos pontos de coleta é
    evolução futura documentada, não implementada aqui)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: RegisterCollectionCommand) -> CollectionDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            trip_repo = SqlAlchemyTripRepository(uow.session)
            history_repo = SqlAlchemyTripStatusHistoryRepository(uow.session)
            collection_repo = SqlAlchemyCollectionRepository(uow.session)

            trip = await trip_repo.get_by_id(command.trip_id)
            if trip is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")

            if await collection_repo.exists_for_trip(command.trip_id):
                raise ConflictError("FREIGHT_COLLECTION_ALREADY_REGISTERED", "Coleta já registrada para esta Viagem.")

            now = datetime.now(timezone.utc)
            collection = Collection.create(viagem_id=command.trip_id, conferencia_ok=command.conferencia_ok, now=now)
            await collection_repo.create(collection)

            trip.mark_collected()
            await trip_repo.add(trip)

            await history_repo.add(
                TripStatusHistoryEntry.create(
                    viagem_id=trip.id,
                    dimensao=StatusHistoryDimension.OPERACIONAL,
                    status=trip.status_operacional.value,
                    usuario_id=command.actor.user_id,
                    origem="portal_gestor",
                    now=now,
                )
            )

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="coletas",
                entidade_id=collection.id,
                acao="CRIACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"conferencia_ok": collection.conferencia_ok},
            )

            await uow.commit()

        return CollectionDTO.from_entity(collection, trip_status_operacional=trip.status_operacional.value)
