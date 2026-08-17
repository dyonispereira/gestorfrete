from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError, ValidationError
from modules.tracking.application.dtos.heartbeat_dto import HeartbeatDTO
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_heartbeat_repository import (
    SqlAlchemyHeartbeatRepository,
)
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_tracking_equipment_repository import (
    SqlAlchemyTrackingEquipmentRepository,
)
from shared_kernel.application.cursor_pagination import decode_cursor, encode_cursor
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListHeartbeatsQuery(Query):
    actor: AuthenticatedActor
    equipment_id: uuid.UUID
    cursor: str | None = None
    limit: int = 20
    received_at_gte: datetime | None = None
    received_at_lte: datetime | None = None


@dataclass(frozen=True)
class ListHeartbeatsResult:
    items: list[HeartbeatDTO]
    next_cursor: str | None
    has_more: bool


class ListHeartbeatsHandler(QueryHandler[ListHeartbeatsQuery, ListHeartbeatsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListHeartbeatsQuery) -> ListHeartbeatsResult:
        after_received_at, after_id = None, None
        if query.cursor is not None:
            try:
                after_received_at, after_id = decode_cursor(query.cursor)
            except ValueError as exc:
                raise ValidationError("TRACKING_INVALID_CURSOR", "Cursor de paginação inválido.") from exc

        async with self._session_factory() as session:
            equipment_repo = SqlAlchemyTrackingEquipmentRepository(session)
            if await equipment_repo.get_by_id(query.equipment_id) is None:
                raise NotFoundError("TRACKING_EQUIPMENT_NOT_FOUND", "Equipamento de Rastreamento não encontrado.")

            repo = SqlAlchemyHeartbeatRepository(session)
            heartbeats = await repo.list_page(
                equipamento_rastreamento_id=query.equipment_id, after_recebido_em=after_received_at,
                after_id=after_id, limit=query.limit + 1, received_at_gte=query.received_at_gte,
                received_at_lte=query.received_at_lte,
            )

        has_more = len(heartbeats) > query.limit
        page = heartbeats[: query.limit]
        next_cursor = encode_cursor(data_hora=page[-1].recebido_em, id=page[-1].id) if has_more and page else None
        return ListHeartbeatsResult(
            items=[HeartbeatDTO.from_entity(h) for h in page], next_cursor=next_cursor, has_more=has_more
        )
