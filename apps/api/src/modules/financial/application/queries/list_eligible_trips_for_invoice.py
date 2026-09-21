from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.financial.application.commands.create_invoice import FISCAL_STATUSES_ALLOWING_INVOICE
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_invoice_trip_repository import (
    SqlAlchemyInvoiceTripRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_delivery_repository import (
    SqlAlchemyDeliveryRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_proof_of_delivery_repository import (
    SqlAlchemyProofOfDeliveryRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor

_MAX_CANDIDATES = 200


@dataclass(frozen=True)
class ListEligibleTripsForInvoiceQuery(Query):
    """Lote Financeiro, Parte 3 — Faturamento Agrupado. "A seleção deve mostrar somente viagens
    faturáveis conforme as regras já existentes" (pedido explícito do usuário) — mesmo critério de
    `CreateInvoiceHandler`: Canhoto registrado + CT-e emitido + ainda não vinculada a uma Fatura
    não cancelada. Lê `freight` (Viagem/Entrega/Canhoto) e a própria `fatura_viagens` — nunca
    `documents` diretamente (D008): `status_fiscal` já é a projeção sincronizada."""

    actor: AuthenticatedActor
    client_id: uuid.UUID


@dataclass(frozen=True)
class EligibleTripDTO:
    trip_id: uuid.UUID
    codigo: str
    data_programada: date | None
    suggested_value: Decimal | None


class ListEligibleTripsForInvoiceHandler(QueryHandler[ListEligibleTripsForInvoiceQuery, list[EligibleTripDTO]]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListEligibleTripsForInvoiceQuery) -> list[EligibleTripDTO]:
        async with self._session_factory() as session:
            trip_repo = SqlAlchemyTripRepository(session)
            delivery_repo = SqlAlchemyDeliveryRepository(session)
            pod_repo = SqlAlchemyProofOfDeliveryRepository(session)
            invoice_trip_repo = SqlAlchemyInvoiceTripRepository(session)

            candidates, _ = await trip_repo.list_page(
                page=1, limit=_MAX_CANDIDATES, status_operacional=None, status_fiscal=None,
                status_financeiro=None, motorista_id=None, veiculo_id=None, cliente_id=query.client_id,
                data_programada=None, codigo=None,
            )

            eligible: list[EligibleTripDTO] = []
            for trip in candidates:
                if trip.status_fiscal not in FISCAL_STATUSES_ALLOWING_INVOICE:
                    continue
                if await invoice_trip_repo.exists_active_for_trip(trip.id):
                    continue
                deliveries = await delivery_repo.list_for_trip(trip.id)
                has_pod = False
                for delivery in deliveries:
                    if await pod_repo.exists_for_delivery(delivery.id):
                        has_pod = True
                        break
                if not has_pod:
                    continue
                eligible.append(
                    EligibleTripDTO(
                        trip_id=trip.id, codigo=trip.codigo, data_programada=trip.data_programada,
                        suggested_value=trip.receita_prevista_snapshot,
                    )
                )
        return eligible
