from __future__ import annotations

import uuid
from datetime import datetime

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, DomainError, NotFoundError
from modules.analytics.domain.entities.consolidated_indicator import ConsolidatedIndicator
from modules.analytics.domain.value_objects.indicator_status import IndicatorStatus
from modules.analytics.infrastructure.persistence.repositories.sqlalchemy_analytical_snapshot_repository import (
    SqlAlchemyAnalyticalSnapshotRepository,
)
from modules.analytics.infrastructure.persistence.repositories.sqlalchemy_consolidated_indicator_repository import (
    SqlAlchemyConsolidatedIndicatorRepository,
)
from modules.analytics.infrastructure.persistence.repositories.sqlalchemy_metric_repository import (
    SqlAlchemyMetricRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)


class AnalyticsCalculationEngine:
    """D420 — mesmo espírito de `TripInternalTransitions`/`FiscalInternalTransitions`/
    `TrackingIngestion`: nunca alcançável por HTTP, só chamado diretamente (por teste hoje; por um
    consumidor de evento/job real quando `Agendamento de Atualização` ganhar um worker de verdade).
    `calculate_trip_revenue_indicator` é a prova mecânica de D090/D149 — lê `viagens.
    receita_realizada` de verdade, cross-module, nunca escreve de volta em `freight`."""

    async def calculate_trip_revenue_indicator(
        self, *, metric_id: uuid.UUID, trip_id: uuid.UUID, now: datetime
    ) -> ConsolidatedIndicator:
        async with SQLAlchemyUnitOfWork() as uow:
            metric_repo = SqlAlchemyMetricRepository(uow.session)
            indicator_repo = SqlAlchemyConsolidatedIndicatorRepository(uow.session)
            trip_repo = SqlAlchemyTripRepository(uow.session)

            metric = await metric_repo.get_by_id(metric_id)
            if metric is None:
                raise NotFoundError("ANALYTICS_METRIC_NOT_FOUND", "Métrica não encontrada.")

            trip = await trip_repo.get_by_id(trip_id)
            if trip is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")
            if trip.receita_realizada is None:
                raise DomainError(
                    "ANALYTICS_TRIP_REVENUE_NOT_AVAILABLE", "Viagem ainda não tem receita realizada."
                )

            periodo_referencia = now.date().isoformat()
            latest = await indicator_repo.get_latest(
                metrica_id=metric.id, dimensao_tipo="VIAGEM", dimensao_id=trip.id,
                periodo_referencia=periodo_referencia,
            )
            if latest is not None and latest.status == IndicatorStatus.SNAPSHOTADO:
                raise ConflictError(
                    "ANALYTICS_INDICATOR_SNAPSHOTTED",
                    "Indicador já está em um Snapshot consolidado — imutável (D151).",
                )
            if latest is not None and latest.status == IndicatorStatus.VALIDO:
                latest.mark_recalculated()
                await indicator_repo.add(latest)

            indicator = ConsolidatedIndicator.calculate(
                metrica_id=metric.id, metrica_versao=metric.versao, dimensao_tipo="VIAGEM",
                dimensao_id=trip.id, periodo_referencia=periodo_referencia, valor=trip.receita_realizada, now=now,
            )
            await indicator_repo.add(indicator)
            await uow.commit()

        return indicator

    async def consolidate_snapshot(
        self, *, snapshot_id: uuid.UUID, indicator_ids: list[uuid.UUID], now: datetime
    ) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            snapshot_repo = SqlAlchemyAnalyticalSnapshotRepository(uow.session)
            indicator_repo = SqlAlchemyConsolidatedIndicatorRepository(uow.session)

            snapshot = await snapshot_repo.get_by_id(snapshot_id)
            if snapshot is None:
                raise NotFoundError("ANALYTICS_SNAPSHOT_NOT_FOUND", "Snapshot não encontrado.")

            for indicator_id in indicator_ids:
                indicator = await indicator_repo.get_by_id(indicator_id)
                if indicator is None:
                    raise NotFoundError("ANALYTICS_INDICATOR_NOT_FOUND", "Indicador Consolidado não encontrado.")
                if indicator.status == IndicatorStatus.SNAPSHOTADO:
                    raise ConflictError(
                        "ANALYTICS_INDICATOR_SNAPSHOTTED", "Indicador já pertence a outro Snapshot consolidado."
                    )
                indicator.mark_snapshotted()
                await indicator_repo.add(indicator)

            await snapshot_repo.link_indicators(snapshot_id, indicator_ids)
            snapshot.consolidate(now=now)
            await snapshot_repo.add(snapshot)
            await uow.commit()
