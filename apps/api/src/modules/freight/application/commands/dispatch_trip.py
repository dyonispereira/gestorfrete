from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.documents.application.commands.create_cte import CreateCteCommand, CreateCteHandler
from modules.drivers.infrastructure.persistence.repositories.sqlalchemy_driver_repository import (
    SqlAlchemyDriverRepository,
)
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_repository import (
    SqlAlchemyVehicleRepository,
)
from modules.freight.application.dtos.trip_dto import TripDTO
from modules.freight.domain.entities.trip_status_history_entry import TripStatusHistoryEntry
from modules.freight.domain.value_objects.status_history_dimension import StatusHistoryDimension
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_status_history_repository import (
    SqlAlchemyTripStatusHistoryRepository,
)
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from modules.notification_center.application.notification_dispatcher import NotificationDispatcher
from modules.notification_center.domain.value_objects.notification_channel import NotificationChannel
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class DispatchTripCommand(Command):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    origin: str  # 'portal_gestor' (commands/dispatch) ou 'app_motorista' (commands/start)


class DispatchTripHandler(CommandHandler[DispatchTripCommand, TripDTO]):
    """`commands/dispatch`/`commands/start` — mesma transição (`LIBERADA→EM_DESLOCAMENTO`), `origin`
    diferente gravado no histórico. D378 — momento em que `nome_motorista_snapshot`/
    `placa_veiculo_snapshot` são congelados pela primeira e única vez. D396 — dispara a criação
    automática do CT-e (`documents`), chamada depois que esta própria transação já commitou (mesmo
    formato "consumidor futuro de evento, síncrono" de D247/D375/D390, primeira vez na direção
    `freight`→`documents`)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()
        self._notifications = NotificationDispatcher()

    async def handle(self, command: DispatchTripCommand) -> TripDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            trip_repo = SqlAlchemyTripRepository(uow.session)
            history_repo = SqlAlchemyTripStatusHistoryRepository(uow.session)
            driver_repo = SqlAlchemyDriverRepository(uow.session)
            vehicle_repo = SqlAlchemyVehicleRepository(uow.session)
            user_repo = SqlAlchemyUserRepository(uow.session)

            trip = await trip_repo.get_by_id(command.trip_id)
            if trip is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")

            driver = await driver_repo.get_by_id(trip.motorista_id) if trip.motorista_id else None
            vehicle = await vehicle_repo.get_by_id(trip.veiculo_tracionador_id) if trip.veiculo_tracionador_id else None

            trip.dispatch(
                nome_motorista_snapshot=driver.nome if driver else "",
                placa_veiculo_snapshot=vehicle.placa if vehicle else "",
            )
            await trip_repo.add(trip)

            now = datetime.now(timezone.utc)
            await history_repo.add(
                TripStatusHistoryEntry.create(
                    viagem_id=trip.id,
                    dimensao=StatusHistoryDimension.OPERACIONAL,
                    status=trip.status_operacional.value,
                    usuario_id=command.actor.user_id,
                    origem=command.origin,
                    now=now,
                )
            )

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="viagens",
                entidade_id=trip.id,
                acao="TRANSICAO_STATUS",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"status_operacional": trip.status_operacional.value},
            )

            # D414 — `ViagemDespachada` notifica o Motorista alocado (link Motorista→Usuário já
            # provado no Lote 9/D408); nunca notifica o próprio ator (Motorista despachando a
            # própria Viagem via `commands/start`).
            if trip.motorista_id is not None:
                driver_user = await user_repo.get_by_driver_id_and_tenant(trip.motorista_id, command.actor.tenant_id)
                if driver_user is not None:
                    await self._notifications.notify(
                        uow.session, usuario_destinatario_id=driver_user.id, actor_user_id=command.actor.user_id,
                        canal=NotificationChannel.IN_APP, evento_origem_tipo="ViagemDespachada",
                        entidade_tipo="VIAGEM", entidade_id=trip.id, titulo="Viagem despachada",
                        mensagem=f"A viagem {trip.codigo} foi despachada e está pronta para deslocamento.", now=now,
                    )

            await uow.commit()

        await CreateCteHandler().handle(CreateCteCommand(actor=command.actor, trip_id=trip.id))

        return TripDTO.from_entity(trip)
