from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError, ValidationError
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_repository import (
    SqlAlchemyVehicleRepository,
)
from modules.tracking.application.dtos.telemetry_reading_dto import TelemetryReadingDTO
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_telemetry_reading_repository import (
    SqlAlchemyTelemetryReadingRepository,
)
from shared_kernel.application.cursor_pagination import decode_cursor, encode_cursor
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListTelemetryReadingsQuery(Query):
    actor: AuthenticatedActor
    vehicle_id: uuid.UUID
    cursor: str | None = None
    limit: int = 20
    sensor_type: str | None = None
    captured_at_gte: datetime | None = None
    captured_at_lte: datetime | None = None
    equipment_id: uuid.UUID | None = None


@dataclass(frozen=True)
class ListTelemetryReadingsResult:
    items: list[TelemetryReadingDTO]
    next_cursor: str | None
    has_more: bool


class ListTelemetryReadingsHandler(QueryHandler[ListTelemetryReadingsQuery, ListTelemetryReadingsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListTelemetryReadingsQuery) -> ListTelemetryReadingsResult:
        after_captured_at, after_id = None, None
        if query.cursor is not None:
            try:
                after_captured_at, after_id = decode_cursor(query.cursor)
            except ValueError as exc:
                raise ValidationError("TRACKING_INVALID_CURSOR", "Cursor de paginação inválido.") from exc

        async with self._session_factory() as session:
            vehicle_repo = SqlAlchemyVehicleRepository(session)
            if await vehicle_repo.get_by_id(query.vehicle_id) is None:
                raise NotFoundError("TRACKING_VEHICLE_NOT_FOUND", "Veículo não encontrado.")

            repo = SqlAlchemyTelemetryReadingRepository(session)
            readings = await repo.list_page(
                veiculo_tracionador_id=query.vehicle_id, after_capturado_em=after_captured_at,
                after_id=after_id, limit=query.limit + 1, sensor_type=query.sensor_type,
                captured_at_gte=query.captured_at_gte, captured_at_lte=query.captured_at_lte,
                equipment_id=query.equipment_id,
            )

        has_more = len(readings) > query.limit
        page = readings[: query.limit]
        next_cursor = encode_cursor(data_hora=page[-1].capturado_em, id=page[-1].id) if has_more and page else None
        return ListTelemetryReadingsResult(
            items=[TelemetryReadingDTO.from_entity(r) for r in page], next_cursor=next_cursor, has_more=has_more
        )
