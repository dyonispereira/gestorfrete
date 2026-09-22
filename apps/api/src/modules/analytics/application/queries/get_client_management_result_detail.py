from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.analytics.application.dtos.management_result_dto import (
    ClientInvoiceSummaryDTO,
    ClientResultDetailDTO,
)
from modules.analytics.application.queries.list_client_management_results import build_client_result
from modules.analytics.application.queries.list_trip_management_results import trip_model_to_result_dto
from modules.analytics.infrastructure.persistence.repositories.management_result_read_repository import (
    ManagementResultReadRepository,
    TripAggregate,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor

_ZERO = Decimal("0")
_ZERO_AGG = TripAggregate(trip_count=0, predicted_revenue=_ZERO, realized_revenue=_ZERO, predicted_cost=_ZERO, realized_cost=_ZERO, km=None)


@dataclass(frozen=True)
class GetClientManagementResultDetailQuery(Query):
    actor: AuthenticatedActor
    client_id: uuid.UUID
    date_from: date | None = None
    date_to: date | None = None


class GetClientManagementResultDetailHandler(
    QueryHandler[GetClientManagementResultDetailQuery, ClientResultDetailDTO]
):
    """Drill-down "Cliente → resultado → Faturas → Viagens → CT-es" (Lote 4). As Faturas listadas
    aqui são as mesmas do módulo Financeiro (`GET /faturas?client_id=`) — sem duplicar dado, só
    somando o essencial para o ranking e apontando de volta para a tela de origem."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetClientManagementResultDetailQuery) -> ClientResultDetailDTO:
        async with self._session_factory() as session:
            repo = ManagementResultReadRepository(session)
            identities = await repo.fetch_client_identities(
                tenant_id=query.actor.tenant_id, client_ids=[query.client_id]
            )
            if query.client_id not in identities:
                raise NotFoundError("ANALYTICS_CLIENT_NOT_FOUND", "Cliente inexistente.")
            name, trade_name = identities[query.client_id]

            trip_aggs = await repo.trip_aggregates_by_client(
                tenant_id=query.actor.tenant_id, date_from=query.date_from, date_to=query.date_to
            )
            result = build_client_result(
                client_id=query.client_id, name=name, trade_name=trade_name,
                trip_agg=trip_aggs.get(query.client_id, _ZERO_AGG),
            )

            trips, _total = await repo.list_trips(
                tenant_id=query.actor.tenant_id, date_from=query.date_from, date_to=query.date_to,
                client_id=query.client_id, page=1, limit=200,
            )
            invoices = await repo.list_invoices_for_client(
                tenant_id=query.actor.tenant_id, client_id=query.client_id,
                date_from=query.date_from, date_to=query.date_to,
            )
            trip_counts = await repo.count_invoice_trips_for_invoices([i.id for i in invoices])

        invoice_summaries = [
            ClientInvoiceSummaryDTO(
                invoice_id=i.id, invoice_number=i.numero_fatura, issue_date=i.data_emissao, status=i.status,
                total_value=i.valor_total, trip_count=trip_counts.get(i.id, 0),
            )
            for i in invoices
        ]
        return ClientResultDetailDTO(
            result=result, trips=[trip_model_to_result_dto(t) for t in trips], invoices=invoice_summaries,
        )
