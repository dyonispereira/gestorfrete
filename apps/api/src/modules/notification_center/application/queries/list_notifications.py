from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.notification_center.application.dtos.notification_dto import NotificationDTO
from modules.notification_center.infrastructure.persistence.repositories.sqlalchemy_notification_repository import (
    SqlAlchemyNotificationRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListNotificationsQuery(Query):
    actor: AuthenticatedActor
    page: int
    limit: int
    channel: str | None
    status: str | None


@dataclass(frozen=True)
class ListNotificationsResult:
    items: list[NotificationDTO]
    total: int


class ListNotificationsHandler(QueryHandler[ListNotificationsQuery, ListNotificationsResult]):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListNotificationsQuery) -> ListNotificationsResult:
        async with self._session_factory() as session:
            repo = SqlAlchemyNotificationRepository(session)
            items, total = await repo.list_page_for_user(
                query.actor.user_id, page=query.page, limit=query.limit, channel=query.channel, status=query.status
            )
            return ListNotificationsResult(items=[NotificationDTO.from_entity(n) for n in items], total=total)
