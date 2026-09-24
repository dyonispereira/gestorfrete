from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError
from modules.freight.application.dtos.manifest_dto import ManifestDTO
from modules.freight.domain.entities.cargo_item import CargoItemSpec
from modules.freight.domain.entities.manifest import Manifest
from modules.freight.domain.entities.trip_status_history_entry import TripStatusHistoryEntry
from modules.freight.domain.value_objects.status_history_dimension import StatusHistoryDimension
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_delivery_repository import (
    SqlAlchemyDeliveryRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_manifest_repository import (
    SqlAlchemyManifestRepository,
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
class ConfirmManifestCommand(Command):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    numero_documento: str | None
    itens: list[CargoItemSpec]


class ConfirmManifestHandler(CommandHandler[ConfirmManifestCommand, ManifestDTO]):
    """`POST /viagens/{id}/romaneios` — V1 Operational Hardening, Parte 2/3. Fecha
    `CARREGANDO → EM_TRANSITO` (com cascata para `EM_ENTREGA` quando já há Entrega `PENDENTE`,
    `018-trip-status.md`) — a segunda transição que até aqui só existia simulada em teste
    (`TripInternalTransitions.confirm_manifest`). Usa exatamente `Trip.mark_manifest_checked()`,
    nenhuma regra nova. Nenhum novo estado — a máquina de estados usada é exatamente a já
    documentada em `002-VIAGEM.md`."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: ConfirmManifestCommand) -> ManifestDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            trip_repo = SqlAlchemyTripRepository(uow.session)
            history_repo = SqlAlchemyTripStatusHistoryRepository(uow.session)
            manifest_repo = SqlAlchemyManifestRepository(uow.session)
            delivery_repo = SqlAlchemyDeliveryRepository(uow.session)

            trip = await trip_repo.get_by_id(command.trip_id)
            if trip is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")

            if await manifest_repo.exists_for_trip(command.trip_id):
                raise ConflictError("FREIGHT_MANIFEST_ALREADY_REGISTERED", "Romaneio já registrado para esta Viagem.")

            manifest = Manifest.create(
                viagem_id=command.trip_id, numero_documento=command.numero_documento, itens=command.itens,
            )
            await manifest_repo.create(manifest)

            has_pending = (await delivery_repo.count_pending_for_trip(command.trip_id)) > 0
            reached = trip.mark_manifest_checked(has_pending_deliveries=has_pending)
            await trip_repo.add(trip)

            now = datetime.now(timezone.utc)
            for status in reached:
                await history_repo.add(
                    TripStatusHistoryEntry.create(
                        viagem_id=trip.id,
                        dimensao=StatusHistoryDimension.OPERACIONAL,
                        status=status.value,
                        usuario_id=command.actor.user_id,
                        origem="portal_gestor",
                        now=now,
                    )
                )

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="romaneios",
                entidade_id=manifest.id,
                acao="CRIACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"numero_documento": manifest.numero_documento, "itens": len(manifest.itens)},
            )

            await uow.commit()

        return ManifestDTO.from_entity(manifest, trip_status_operacional=trip.status_operacional.value)
