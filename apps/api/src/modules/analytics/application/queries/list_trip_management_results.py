from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.analytics.application.dtos.management_result_dto import TripResultDTO, build_totals
from modules.analytics.infrastructure.persistence.repositories.management_result_read_repository import (
    ManagementResultReadRepository,
    TripAggregate,
)
from modules.freight.infrastructure.persistence.models.trip_model import TripModel
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListTripManagementResultsQuery(Query):
    actor: AuthenticatedActor
    date_from: date | None = None
    date_to: date | None = None
    client_id: uuid.UUID | None = None
    vehicle_id: uuid.UUID | None = None
    driver_id: uuid.UUID | None = None
    page: int = 1
    limit: int = 20


@dataclass(frozen=True)
class ListTripManagementResultsResult:
    items: list[TripResultDTO]
    total: int


def trip_model_to_result_dto(trip: TripModel) -> TripResultDTO:
    agg = TripAggregate(
        trip_count=1,
        predicted_revenue=trip.receita_prevista_snapshot if trip.receita_prevista_snapshot is not None else Decimal("0"),
        realized_revenue=trip.receita_realizada if trip.receita_realizada is not None else Decimal("0"),
        predicted_cost=trip.custo_previsto if trip.custo_previsto is not None else Decimal("0"),
        realized_cost=trip.custo_realizado if trip.custo_realizado is not None else Decimal("0"),
        km=trip.km_rodado,
    )
    return TripResultDTO(
        trip_id=trip.id, codigo=trip.codigo, data_programada=trip.data_programada,
        client_id=trip.cliente_id, client_name=(trip.cliente_snapshot or {}).get("razao_social"),
        driver_id=trip.motorista_id, driver_name=trip.nome_motorista_snapshot,
        vehicle_id=trip.veiculo_tracionador_id, vehicle_plate=trip.placa_veiculo_snapshot,
        totals=build_totals(agg),
    )


class ListTripManagementResultsHandler(
    QueryHandler[ListTripManagementResultsQuery, ListTripManagementResultsResult]
):
    """Dimensão Viagem do Resultado Gerencial (Lote 4) — lê `Trip` diretamente, os mesmos campos já
    autoritativos usados na aba Financeiro da Viagem (nunca recalculados aqui)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListTripManagementResultsQuery) -> ListTripManagementResultsResult:
        async with self._session_factory() as session:
            repo = ManagementResultReadRepository(session)
            trips, total = await repo.list_trips(
                tenant_id=query.actor.tenant_id, date_from=query.date_from, date_to=query.date_to,
                client_id=query.client_id, vehicle_id=query.vehicle_id, driver_id=query.driver_id,
                page=query.page, limit=query.limit,
            )
        return ListTripManagementResultsResult(items=[trip_model_to_result_dto(t) for t in trips], total=total)
