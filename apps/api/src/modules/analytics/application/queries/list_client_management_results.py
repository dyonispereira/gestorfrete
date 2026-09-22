from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.analytics.application.dtos.management_result_dto import ClientResultDTO, build_totals
from modules.analytics.infrastructure.persistence.repositories.management_result_read_repository import (
    ManagementResultReadRepository,
    TripAggregate,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListClientManagementResultsQuery(Query):
    actor: AuthenticatedActor
    date_from: date | None = None
    date_to: date | None = None


def build_client_result(
    *, client_id: uuid.UUID, name: str, trade_name: str | None, trip_agg: TripAggregate
) -> ClientResultDTO:
    return ClientResultDTO(client_id=client_id, name=name, trade_name=trade_name, totals=build_totals(trip_agg))


class ListClientManagementResultsHandler(QueryHandler[ListClientManagementResultsQuery, list[ClientResultDTO]]):
    """Dimensão Cliente do Resultado Gerencial (Lote 4). Escopo deliberado (D008-consistente):
    "Custo" aqui é só o custo operacional de Viagem atribuível ao Cliente (`Trip.custo_realizado`
    das Viagens dele) — nunca rateia Manutenção/frota por Cliente, o que exigiria uma regra de
    alocação inventada sem base nos contratos atuais (gap registrado em
    docs/domain/012-resultado-gerencial.md, não aproximado)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListClientManagementResultsQuery) -> list[ClientResultDTO]:
        async with self._session_factory() as session:
            repo = ManagementResultReadRepository(session)
            trip_aggs = await repo.trip_aggregates_by_client(
                tenant_id=query.actor.tenant_id, date_from=query.date_from, date_to=query.date_to
            )
            identities = await repo.fetch_client_identities(
                tenant_id=query.actor.tenant_id, client_ids=list(trip_aggs)
            )

        results = [
            build_client_result(
                client_id=client_id, name=identities[client_id][0], trade_name=identities[client_id][1],
                trip_agg=agg,
            )
            for client_id, agg in trip_aggs.items()
            if client_id in identities
        ]
        results.sort(key=lambda r: r.totals.realized_revenue, reverse=True)
        return results
