from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.freight.application.dtos.occurrence_dto import OccurrenceDTO
from modules.freight.domain.entities.occurrence import Occurrence
from modules.freight.domain.value_objects.occurrence_severity import OccurrenceSeverity
from modules.freight.domain.value_objects.occurrence_type import OccurrenceType
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_occurrence_repository import (
    SqlAlchemyOccurrenceRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from modules.notification_center.application.notification_dispatcher import NotificationDispatcher
from modules.notification_center.domain.value_objects.notification_channel import NotificationChannel
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateOccurrenceCommand(Command):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    tipo: OccurrenceType
    descricao: str
    gravidade: OccurrenceSeverity | None
    occurred_at: datetime


class CreateOccurrenceHandler(CommandHandler[CreateOccurrenceCommand, OccurrenceDTO]):
    """Publica `OcorrenciaRegistrada` sempre e também `AvariaRegistrada` quando `tipo=AVARIA`
    (`017-trip-occurrences.md`) — documentado, não literalmente despachado a um EventBus (nenhum
    módulo deste backend publica eventos de verdade ainda, RabbitMQ fora deste ambiente, mesma
    situação de todo lote anterior). **Não** move `Trip.status_operacional` para `INTERROMPIDA`
    automaticamente — ação deliberadamente separada."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()
        self._notifications = NotificationDispatcher()

    async def handle(self, command: CreateOccurrenceCommand) -> OccurrenceDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            trip_repo = SqlAlchemyTripRepository(uow.session)
            occurrence_repo = SqlAlchemyOccurrenceRepository(uow.session)

            trip = await trip_repo.get_by_id(command.trip_id)
            if trip is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")

            occurrence = Occurrence.create(
                viagem_id=command.trip_id,
                tipo=command.tipo,
                descricao=command.descricao,
                gravidade=command.gravidade,
                occurred_at=command.occurred_at,
            )
            await occurrence_repo.add(occurrence)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="ocorrencias",
                entidade_id=occurrence.id,
                acao="CRIACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"tipo": occurrence.tipo.value, "descricao": occurrence.descricao},
            )

            # D414 — `OcorrenciaRegistrada` notifica quem criou a Viagem (`viagens.criado_por`,
            # snapshot já existente, nenhum dado novo); nunca notifica o próprio ator.
            if trip.audit.created_by is not None:
                await self._notifications.notify(
                    uow.session, usuario_destinatario_id=trip.audit.created_by, actor_user_id=command.actor.user_id,
                    canal=NotificationChannel.IN_APP, evento_origem_tipo="OcorrenciaRegistrada",
                    entidade_tipo="VIAGEM", entidade_id=trip.id, titulo="Nova ocorrência registrada",
                    mensagem=f"Ocorrência ({occurrence.tipo.value}) registrada na viagem {trip.codigo}.",
                    now=datetime.now(timezone.utc),
                )

            await uow.commit()

        return OccurrenceDTO.from_entity(occurrence)
