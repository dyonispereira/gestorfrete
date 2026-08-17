from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from modules.notification_center.application.dtos.notification_dto import ChannelPreferenceDTO
from modules.notification_center.domain.value_objects.notification_channel import NotificationChannel
from modules.notification_center.infrastructure.persistence.repositories.sqlalchemy_channel_preference_repository import (
    SqlAlchemyChannelPreferenceRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ListChannelPreferencesQuery(Query):
    actor: AuthenticatedActor


class ListChannelPreferencesHandler(QueryHandler[ListChannelPreferencesQuery, list[ChannelPreferenceDTO]]):
    """Sempre os três canais presentes na resposta — default `enabled=True` quando nenhuma
    preferência foi salva ainda (`086-notifications.md`)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: ListChannelPreferencesQuery) -> list[ChannelPreferenceDTO]:
        async with self._session_factory() as session:
            repo = SqlAlchemyChannelPreferenceRepository(session)
            saved = await repo.list_for_user(query.actor.user_id)

        saved_by_channel = {p.canal: p for p in saved}
        return [
            ChannelPreferenceDTO(channel=channel.value, enabled=saved_by_channel[channel].habilitado)
            if channel in saved_by_channel
            else ChannelPreferenceDTO(channel=channel.value, enabled=True)
            for channel in NotificationChannel
        ]
