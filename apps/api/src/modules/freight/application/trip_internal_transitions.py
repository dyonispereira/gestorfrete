from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.freight.domain.entities.trip_status_history_entry import TripStatusHistoryEntry
from modules.freight.domain.value_objects.status_history_dimension import StatusHistoryDimension
from modules.freight.domain.value_objects.trip_financial_status import TripFinancialStatus
from modules.freight.domain.value_objects.trip_fiscal_status import TripFiscalStatus
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_delivery_repository import (
    SqlAlchemyDeliveryRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_status_history_repository import (
    SqlAlchemyTripStatusHistoryRepository,
)


class TripInternalTransitions:
    """D376/D375 — ponte cross-módulo, não-HTTP, para outros módulos dispararem transições de
    `Trip` sem que `freight` precise expor um comando dedicado para cada gatilho externo (mesmo
    padrão do `VehicleAvailabilityProjector`, Lote 4, D247). `await_checklist`/`approve_checklist`
    já são chamados por handlers HTTP reais (`maintenance.CreateChecklistHandler`/
    `ApproveChecklistHandler`) desde que o módulo Checklist foi implementado — não são mais
    simulação. Os demais métodos ainda simulam consumidores de evento que este lote não
    implementa, ou (no caso de `register_collection`/`confirm_manifest`) ficaram órfãos depois que
    Coleta/Romaneio ganharam seus próprios comandos, que chamam `Trip.mark_collected`/
    `mark_manifest_checked` diretamente."""

    async def await_checklist(self, *, trip_id: uuid.UUID, now: datetime) -> None:
        """Gatilho "pronta para a data/rota programada" — `PLANEJADA→AGUARDANDO_CHECKLIST`.
        Chamado por `maintenance.CreateChecklistHandler` ao criar um Checklist para esta Viagem
        (`018-trip-status.md`)."""

        async with SQLAlchemyUnitOfWork() as uow:
            trip_repo = SqlAlchemyTripRepository(uow.session)
            history_repo = SqlAlchemyTripStatusHistoryRepository(uow.session)
            trip = await trip_repo.get_by_id(trip_id)
            if trip is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")
            trip.await_checklist()
            await trip_repo.add(trip)
            await history_repo.add(
                TripStatusHistoryEntry.create(
                    viagem_id=trip.id,
                    dimensao=StatusHistoryDimension.OPERACIONAL,
                    status=trip.status_operacional.value,
                    usuario_id=None,
                    origem="sistema",
                    now=now,
                )
            )
            await uow.commit()

    async def approve_checklist(self, *, trip_id: uuid.UUID, now: datetime) -> None:
        """`ChecklistAprovado` — `AGUARDANDO_CHECKLIST→LIBERADA`. Chamado por
        `maintenance.ApproveChecklistHandler` ao aprovar o Checklist desta Viagem."""

        async with SQLAlchemyUnitOfWork() as uow:
            trip_repo = SqlAlchemyTripRepository(uow.session)
            history_repo = SqlAlchemyTripStatusHistoryRepository(uow.session)
            trip = await trip_repo.get_by_id(trip_id)
            if trip is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")
            trip.release_after_checklist()
            await trip_repo.add(trip)
            await history_repo.add(
                TripStatusHistoryEntry.create(
                    viagem_id=trip.id,
                    dimensao=StatusHistoryDimension.OPERACIONAL,
                    status=trip.status_operacional.value,
                    usuario_id=None,
                    origem="sistema",
                    now=now,
                    observacao="Checklist aprovado.",
                )
            )
            await uow.commit()

    async def register_collection(self, *, trip_id: uuid.UUID, now: datetime) -> None:
        """Simula o futuro endpoint de Coleta — `EM_DESLOCAMENTO→CARREGANDO`."""

        async with SQLAlchemyUnitOfWork() as uow:
            trip_repo = SqlAlchemyTripRepository(uow.session)
            history_repo = SqlAlchemyTripStatusHistoryRepository(uow.session)
            trip = await trip_repo.get_by_id(trip_id)
            if trip is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")
            trip.mark_collected()
            await trip_repo.add(trip)
            await history_repo.add(
                TripStatusHistoryEntry.create(
                    viagem_id=trip.id,
                    dimensao=StatusHistoryDimension.OPERACIONAL,
                    status=trip.status_operacional.value,
                    usuario_id=None,
                    origem="sistema",
                    now=now,
                    observacao="Coleta registrada (simulação — sem endpoint de Coleta neste lote).",
                )
            )
            await uow.commit()

    async def confirm_manifest(self, *, trip_id: uuid.UUID, now: datetime) -> None:
        """Simula o futuro endpoint de Romaneio conferido — `CARREGANDO→EM_TRANSITO` (+ cascata
        para `EM_ENTREGA` quando já há Entrega `PENDENTE`)."""

        async with SQLAlchemyUnitOfWork() as uow:
            trip_repo = SqlAlchemyTripRepository(uow.session)
            history_repo = SqlAlchemyTripStatusHistoryRepository(uow.session)
            delivery_repo = SqlAlchemyDeliveryRepository(uow.session)
            trip = await trip_repo.get_by_id(trip_id)
            if trip is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")
            has_pending = (await delivery_repo.count_pending_for_trip(trip_id)) > 0
            reached = trip.mark_manifest_checked(has_pending_deliveries=has_pending)
            await trip_repo.add(trip)
            for status in reached:
                await history_repo.add(
                    TripStatusHistoryEntry.create(
                        viagem_id=trip.id,
                        dimensao=StatusHistoryDimension.OPERACIONAL,
                        status=status.value,
                        usuario_id=None,
                        origem="sistema",
                        now=now,
                        observacao="Romaneio conferido (simulação — sem endpoint de Romaneio neste lote)."
                        if status == reached[0]
                        else None,
                    )
                )
            await uow.commit()

    async def update_realized_cost(self, *, trip_id: uuid.UUID, value: Decimal) -> None:
        """D390/D392 — chamado por `financial` (Rateio de Despesa criado/removido em uma Conta a
        Pagar com `origin=VIAGEM`). `value` já é a soma total dos rateios da viagem, nunca um
        incremento — o chamador recalcula o total antes de chamar."""

        async with SQLAlchemyUnitOfWork() as uow:
            trip_repo = SqlAlchemyTripRepository(uow.session)
            trip = await trip_repo.get_by_id(trip_id)
            if trip is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")
            trip.update_realized_cost(value=value)
            await trip_repo.add(trip)
            await uow.commit()

    async def update_realized_revenue(self, *, trip_id: uuid.UUID, value: Decimal) -> None:
        """D390/D392 — chamado por `financial` (`commands/confirm-receipt`)."""

        async with SQLAlchemyUnitOfWork() as uow:
            trip_repo = SqlAlchemyTripRepository(uow.session)
            trip = await trip_repo.get_by_id(trip_id)
            if trip is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")
            trip.update_realized_revenue(value=value)
            await trip_repo.add(trip)
            await uow.commit()

    async def update_km_rodado(self, *, trip_id: uuid.UUID, value: Decimal | None) -> None:
        """V1 Operational Hardening, Parte 2 — chamado por `TripOdometerRecorder` (`fleet`) depois
        que a leitura de encerramento é pareada com a de despacho."""

        async with SQLAlchemyUnitOfWork() as uow:
            trip_repo = SqlAlchemyTripRepository(uow.session)
            trip = await trip_repo.get_by_id(trip_id)
            if trip is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")
            trip.update_km_rodado(value=value)
            await trip_repo.add(trip)
            await uow.commit()

    async def record_fiscal_transition(self, *, trip_id: uuid.UUID, status: TripFiscalStatus, now: datetime) -> None:
        """Simula o futuro consumidor de evento de `documents` (D375)."""

        async with SQLAlchemyUnitOfWork() as uow:
            trip_repo = SqlAlchemyTripRepository(uow.session)
            history_repo = SqlAlchemyTripStatusHistoryRepository(uow.session)
            trip = await trip_repo.get_by_id(trip_id)
            if trip is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")
            trip.record_fiscal_transition(status)
            await trip_repo.add(trip)
            await history_repo.add(
                TripStatusHistoryEntry.create(
                    viagem_id=trip.id,
                    dimensao=StatusHistoryDimension.FISCAL,
                    status=status.value,
                    usuario_id=None,
                    origem="sistema",
                    now=now,
                )
            )
            await uow.commit()

    async def record_financial_transition(
        self, *, trip_id: uuid.UUID, status: TripFinancialStatus, now: datetime
    ) -> None:
        """Simula o futuro consumidor de evento de `financial` (D375)."""

        async with SQLAlchemyUnitOfWork() as uow:
            trip_repo = SqlAlchemyTripRepository(uow.session)
            history_repo = SqlAlchemyTripStatusHistoryRepository(uow.session)
            trip = await trip_repo.get_by_id(trip_id)
            if trip is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")
            trip.record_financial_transition(status)
            await trip_repo.add(trip)
            await history_repo.add(
                TripStatusHistoryEntry.create(
                    viagem_id=trip.id,
                    dimensao=StatusHistoryDimension.FINANCEIRO,
                    status=status.value,
                    usuario_id=None,
                    origem="sistema",
                    now=now,
                )
            )
            await uow.commit()
