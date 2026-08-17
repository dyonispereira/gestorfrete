from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError, ValidationError
from modules.fleet.application.dtos.odometer_reading_dto import OdometerReadingDTO
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_odometer_reading_repository import (
    SqlAlchemyOdometerReadingRepository,
)
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_repository import (
    SqlAlchemyVehicleRepository,
)
from shared_kernel.application.cursor_pagination import decode_cursor, encode_cursor
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListOdometerReadingsQuery(Query):
    actor: AuthenticatedActor
    vehicle_id: uuid.UUID
    cursor: str | None = None
    limit: int = 20
    origem: str | None = None


@dataclass(frozen=True)
class ListOdometerReadingsResult:
    items: list[OdometerReadingDTO]
    next_cursor: str | None
    has_more: bool


class ListOdometerReadingsHandler(QueryHandler[ListOdometerReadingsQuery, ListOdometerReadingsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListOdometerReadingsQuery) -> ListOdometerReadingsResult:
        after_data_hora: datetime | None = None
        after_id: uuid.UUID | None = None
        if query.cursor is not None:
            try:
                after_data_hora, after_id = decode_cursor(query.cursor)
            except ValueError as exc:
                raise ValidationError("FLEET_INVALID_CURSOR", "Cursor de paginação inválido.") from exc

        async with self._session_factory() as session:
            vehicle_repo = SqlAlchemyVehicleRepository(session)
            if await vehicle_repo.get_by_id(query.vehicle_id) is None:
                raise NotFoundError("FLEET_VEHICLE_NOT_FOUND", "Veículo não encontrado.")

            repo = SqlAlchemyOdometerReadingRepository(session)
            # Busca um a mais para saber se há próxima página sem depender do tamanho da última
            # (`PAGINATION.md`: nunca inferir `has_more` pelo tamanho da página retornada).
            readings = await repo.list_for_vehicle_cursor(
                veiculo_tracionador_id=query.vehicle_id, limit=query.limit + 1, origem=query.origem,
                after_data_hora=after_data_hora, after_id=after_id,
            )

        has_more = len(readings) > query.limit
        page = readings[: query.limit]
        next_cursor = encode_cursor(data_hora=page[-1].data_hora, id=page[-1].id) if has_more and page else None

        return ListOdometerReadingsResult(
            items=[OdometerReadingDTO.from_entity(r) for r in page], next_cursor=next_cursor, has_more=has_more
        )
