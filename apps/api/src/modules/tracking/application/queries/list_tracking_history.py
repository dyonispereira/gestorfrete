from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import DomainError, NotFoundError, ValidationError
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_repository import (
    SqlAlchemyVehicleRepository,
)
from modules.identity_access.application.authorization_service import AuthorizationService
from modules.tracking.application.dtos.tracking_history_entry_dto import TrackingHistoryEntryDTO
from modules.tracking.application.queries.tracking_event_permission_map import EVENT_TYPE_PERMISSION
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_telemetry_reading_repository import (
    SqlAlchemyTelemetryReadingRepository,
)
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_tracking_event_repository import (
    SqlAlchemyTrackingEventRepository,
)
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_vehicle_position_repository import (
    SqlAlchemyVehiclePositionRepository,
)
from shared_kernel.application.cursor_pagination import decode_cursor, encode_cursor
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListTrackingHistoryQuery(Query):
    actor: AuthenticatedActor
    vehicle_id: uuid.UUID
    period_start: datetime | None
    period_end: datetime | None
    cursor: str | None = None
    limit: int = 20
    source: str | None = None


@dataclass(frozen=True)
class ListTrackingHistoryResult:
    items: list[TrackingHistoryEntryDTO]
    next_cursor: str | None
    has_more: bool


class ListTrackingHistoryHandler(QueryHandler[ListTrackingHistoryQuery, ListTrackingHistoryResult]):
    """D290 — Read Model composto, nenhuma tabela nova. Correção de k-way merge: buscar `limit + 1`
    de cada fonte já ordenada/cortada pelo cursor é suficiente para montar o top `limit + 1` da união
    — o item de rank K de uma união de streams ordenados nunca está além da posição K em nenhum
    stream individual."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._authz = AuthorizationService(session_factory)

    async def handle(self, query: ListTrackingHistoryQuery) -> ListTrackingHistoryResult:
        if query.period_start is None or query.period_end is None:
            raise DomainError(
                "TRACKING_HISTORY_PERIOD_REQUIRED", "period_start e period_end são obrigatórios."
            )

        after_data_hora, after_id = None, None
        if query.cursor is not None:
            try:
                after_data_hora, after_id = decode_cursor(query.cursor)
            except ValueError as exc:
                raise ValidationError("TRACKING_INVALID_CURSOR", "Cursor de paginação inválido.") from exc

        fetch_limit = query.limit + 1
        candidates: list[TrackingHistoryEntryDTO] = []

        async with self._session_factory() as session:
            vehicle_repo = SqlAlchemyVehicleRepository(session)
            if await vehicle_repo.get_by_id(query.vehicle_id) is None:
                raise NotFoundError("TRACKING_VEHICLE_NOT_FOUND", "Veículo não encontrado.")

            granted_codes = await self._authz.get_permission_codes(query.actor)

            if query.source in (None, "POSICAO"):
                position_repo = SqlAlchemyVehiclePositionRepository(session)
                positions = await position_repo.list_page(
                    veiculo_tracionador_id=query.vehicle_id, after_capturado_em=after_data_hora,
                    after_id=after_id, limit=fetch_limit, captured_at_gte=query.period_start,
                    captured_at_lte=query.period_end, origin_id=None, equipment_id=None,
                )
                candidates.extend(
                    TrackingHistoryEntryDTO(
                        occurred_at=p.capturado_em, source="POSICAO",
                        summary=f"Posição capturada ({p.localizacao.latitude}, {p.localizacao.longitude})",
                        reference_id=p.id,
                    )
                    for p in positions
                )

            if query.source in (None, "TELEMETRIA") and "tracking.telemetry.view" in granted_codes:
                telemetry_repo = SqlAlchemyTelemetryReadingRepository(session)
                readings = await telemetry_repo.list_page(
                    veiculo_tracionador_id=query.vehicle_id, after_capturado_em=after_data_hora,
                    after_id=after_id, limit=fetch_limit, sensor_type=None, captured_at_gte=query.period_start,
                    captured_at_lte=query.period_end, equipment_id=None,
                )
                candidates.extend(
                    TrackingHistoryEntryDTO(
                        occurred_at=r.capturado_em, source="TELEMETRIA",
                        summary=f"{r.tipo_sensor.value}: {r.valor} {r.unidade}", reference_id=r.id,
                    )
                    for r in readings
                )

            if query.source in (None, "EVENTO"):
                allowed_types = [t.value for t, code in EVENT_TYPE_PERMISSION.items() if code in granted_codes]
                if allowed_types:
                    event_repo = SqlAlchemyTrackingEventRepository(session)
                    events = await event_repo.list_page(
                        after_data_hora=after_data_hora, after_id=after_id, limit=fetch_limit, types=allowed_types,
                        severity=None, vehicle_id=query.vehicle_id, occurred_at_gte=query.period_start,
                        occurred_at_lte=query.period_end,
                    )
                    candidates.extend(
                        TrackingHistoryEntryDTO(
                            occurred_at=e.data_hora, source="EVENTO",
                            summary=f"{e.tipo.value} (severidade {e.severidade.value})", reference_id=e.id,
                        )
                        for e in events
                    )

        candidates.sort(key=lambda c: (c.occurred_at, c.reference_id), reverse=True)
        has_more = len(candidates) > query.limit
        page = candidates[: query.limit]
        next_cursor = encode_cursor(data_hora=page[-1].occurred_at, id=page[-1].reference_id) if has_more and page else None
        return ListTrackingHistoryResult(items=page, next_cursor=next_cursor, has_more=has_more)
