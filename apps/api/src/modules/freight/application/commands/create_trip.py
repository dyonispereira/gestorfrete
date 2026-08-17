from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ValidationError
from modules.freight.application.dtos.trip_dto import TripDTO
from modules.freight.domain.entities.trip import Trip
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor
from shared_kernel.domain.audit_metadata import AuditMetadata


@dataclass(frozen=True)
class CreateTripCommand(Command):
    actor: AuthenticatedActor
    cliente_id: uuid.UUID
    data_programada: date | None
    janela_programada: datetime | None


class CreateTripHandler(CommandHandler[CreateTripCommand, TripDTO]):
    """D378 — `cliente_snapshot` é congelado aqui, no momento da criação (`cliente_id` já
    obrigatório). Nunca toca em `alocacoes_recurso_viagem` — alocação inicial é um passo separado
    (`016-trip-resources.md`)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateTripCommand) -> TripDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyTripRepository(uow.session)

            cliente_snapshot = await repo.get_client_snapshot(command.cliente_id)
            if cliente_snapshot is None:
                raise ValidationError("FREIGHT_UNKNOWN_CLIENT_ID", "Cliente inexistente.")

            now = datetime.now(timezone.utc)
            trip = Trip.create(
                cliente_id=command.cliente_id,
                data_programada=command.data_programada,
                janela_programada=command.janela_programada,
                cliente_snapshot=cliente_snapshot,
                now=now,
                audit=AuditMetadata(
                    created_at=now, created_by=command.actor.user_id, updated_at=now, updated_by=command.actor.user_id
                ),
            )
            await repo.add(trip)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="viagens",
                entidade_id=trip.id,
                acao="CRIACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"codigo": trip.codigo, "cliente_id": str(trip.cliente_id)},
            )

            await uow.commit()

        return TripDTO.from_entity(trip)
