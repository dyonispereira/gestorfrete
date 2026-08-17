from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.freight.application.dtos.trip_financials_view_dto import TripFinancialsViewDTO
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor

PREDICTED_PERMISSION = "financial.trip_predicted_value.view"
ACTUAL_PERMISSION = "financial.trip_actual_value.view"
MARGIN_PERMISSION = "financial.trip_margin.view"


@dataclass(frozen=True)
class GetTripFinancialsQuery(Query):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    held_permissions: frozenset[str]


class GetTripFinancialsHandler(QueryHandler[GetTripFinancialsQuery, TripFinancialsViewDTO]):
    """D389 — vive em `freight` (D262), não `financial`; só o RBAC checado aqui pertence a
    `financial` (D267-style granularidade de campo)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetTripFinancialsQuery) -> TripFinancialsViewDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyTripRepository(session)
            trip = await repo.get_by_id(query.trip_id)
        if trip is None:
            raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")

        has_predicted = PREDICTED_PERMISSION in query.held_permissions
        has_actual = ACTUAL_PERMISSION in query.held_permissions
        has_margin = MARGIN_PERMISSION in query.held_permissions

        return TripFinancialsViewDTO(
            financial_status=trip.status_financeiro.value,
            predicted_revenue=trip.receita_prevista_snapshot if has_predicted else None,
            predicted_cost=trip.custo_previsto if has_predicted else None,
            predicted_margin=trip.margem_prevista if has_predicted else None,
            actual_revenue=trip.receita_realizada if has_actual else None,
            actual_cost=trip.custo_realizado if has_actual else None,
            actual_margin=trip.margem_realizada if has_margin else None,
            financial_deviation=trip.desvio_financeiro if has_margin else None,
        )
