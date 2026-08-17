from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import AuthorizationError, NotFoundError
from modules.notification_center.application.dtos.notification_dto import NotificationDTO
from modules.notification_center.infrastructure.persistence.repositories.sqlalchemy_notification_repository import (
    SqlAlchemyNotificationRepository,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class GetNotificationQuery(Query):
    actor: AuthenticatedActor
    notification_id: uuid.UUID


class GetNotificationHandler(QueryHandler[GetNotificationQuery, NotificationDTO]):
    """`086` — `403`, nunca `404`, quando pertence a outro usuário: notificação é sempre pessoal,
    mesmo para Gestor com toda permissão."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def handle(self, query: GetNotificationQuery) -> NotificationDTO:
        async with self._session_factory() as session:
            repo = SqlAlchemyNotificationRepository(session)
            notification = await repo.get_by_id(query.notification_id)
        if notification is None:
            raise NotFoundError("NOTIFICATION_NOT_FOUND", "Notificação não encontrada.")
        if notification.usuario_destinatario_id != query.actor.user_id:
            raise AuthorizationError("NOTIFICATION_FORBIDDEN", "Notificação não pertence ao usuário autenticado.")
        return NotificationDTO.from_entity(notification)
