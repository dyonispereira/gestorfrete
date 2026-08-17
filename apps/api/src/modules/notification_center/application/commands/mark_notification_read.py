from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import AuthorizationError, NotFoundError
from modules.notification_center.application.dtos.notification_dto import NotificationDTO
from modules.notification_center.infrastructure.persistence.repositories.sqlalchemy_notification_repository import (
    SqlAlchemyNotificationRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class MarkNotificationReadCommand(Command):
    actor: AuthenticatedActor
    notification_id: uuid.UUID


class MarkNotificationReadHandler(CommandHandler[MarkNotificationReadCommand, NotificationDTO]):
    async def handle(self, command: MarkNotificationReadCommand) -> NotificationDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyNotificationRepository(uow.session)
            notification = await repo.get_by_id(command.notification_id)
            if notification is None:
                raise NotFoundError("NOTIFICATION_NOT_FOUND", "Notificação não encontrada.")
            if notification.usuario_destinatario_id != command.actor.user_id:
                raise AuthorizationError(
                    "NOTIFICATION_FORBIDDEN", "Notificação não pertence ao usuário autenticado."
                )

            notification.mark_read(now=datetime.now(timezone.utc))
            await repo.add(notification)
            await uow.commit()

        return NotificationDTO.from_entity(notification)
