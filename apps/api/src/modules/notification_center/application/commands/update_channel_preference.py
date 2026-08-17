from __future__ import annotations

from dataclasses import dataclass

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from modules.notification_center.application.dtos.notification_dto import ChannelPreferenceDTO
from modules.notification_center.domain.entities.channel_preference import ChannelPreference
from modules.notification_center.domain.value_objects.notification_channel import NotificationChannel
from modules.notification_center.infrastructure.persistence.repositories.sqlalchemy_channel_preference_repository import (
    SqlAlchemyChannelPreferenceRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateChannelPreferenceCommand(Command):
    actor: AuthenticatedActor
    channel: NotificationChannel
    enabled: bool


class UpdateChannelPreferenceHandler(CommandHandler[UpdateChannelPreferenceCommand, ChannelPreferenceDTO]):
    """Sempre a própria preferência (resolvida da sessão, sem parâmetro de usuário no path)."""

    async def handle(self, command: UpdateChannelPreferenceCommand) -> ChannelPreferenceDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyChannelPreferenceRepository(uow.session)
            preference = await repo.get(command.actor.user_id, command.channel)
            if preference is None:
                preference = ChannelPreference.create(
                    usuario_id=command.actor.user_id, canal=command.channel, habilitado=command.enabled
                )
            else:
                preference.habilitado = command.enabled
            await repo.add(preference)
            await uow.commit()

        return ChannelPreferenceDTO.from_entity(preference)
