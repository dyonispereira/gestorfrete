from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from modules.notification_center.domain.entities.notification import Notification
from modules.notification_center.domain.value_objects.notification_channel import NotificationChannel
from modules.notification_center.infrastructure.persistence.repositories.sqlalchemy_channel_preference_repository import (
    SqlAlchemyChannelPreferenceRepository,
)
from modules.notification_center.infrastructure.persistence.repositories.sqlalchemy_notification_repository import (
    SqlAlchemyNotificationRepository,
)


class NotificationDispatcher:
    """D414/D320 — chamado **sincronamente**, na mesma transação/sessão do Handler que publica o
    evento de origem (nunca via RabbitMQ — a criação da linha `notificacoes` não pode depender de um
    worker existir). Consulta `Preferência de Canal` antes de criar: canal desabilitado = nenhuma
    linha criada, nunca uma Notificação "descartada" registrada."""

    async def notify(
        self, session: AsyncSession, *, usuario_destinatario_id: uuid.UUID, actor_user_id: uuid.UUID,
        canal: NotificationChannel, evento_origem_tipo: str, entidade_tipo: str | None, entidade_id: uuid.UUID | None,
        titulo: str, mensagem: str, now: datetime,
    ) -> None:
        if usuario_destinatario_id == actor_user_id:
            # Nunca notifica alguém da própria ação (D414).
            return

        preference_repo = SqlAlchemyChannelPreferenceRepository(session)
        preference = await preference_repo.get(usuario_destinatario_id, canal)
        if preference is not None and not preference.habilitado:
            return

        notification = Notification.dispatch(
            usuario_destinatario_id=usuario_destinatario_id, canal=canal, evento_origem_tipo=evento_origem_tipo,
            entidade_tipo=entidade_tipo, entidade_id=entidade_id, titulo=titulo, mensagem=mensagem, now=now,
        )
        await SqlAlchemyNotificationRepository(session).add(notification)
