from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.notification_center.domain.entities.channel_preference import ChannelPreference
from modules.notification_center.domain.entities.notification import Notification


@dataclass(frozen=True)
class NotificationDTO:
    id: uuid.UUID
    channel: str
    origin_event_type: str
    entity_type: str | None
    entity_id: uuid.UUID | None
    title: str
    message: str
    status: str
    sent_at: datetime
    read_at: datetime | None

    @staticmethod
    def from_entity(notification: Notification) -> "NotificationDTO":
        return NotificationDTO(
            id=notification.id, channel=notification.canal.value, origin_event_type=notification.evento_origem_tipo,
            entity_type=notification.entidade_tipo, entity_id=notification.entidade_id, title=notification.titulo,
            message=notification.mensagem, status=notification.status.value, sent_at=notification.enviado_em,
            read_at=notification.lido_em,
        )


@dataclass(frozen=True)
class ChannelPreferenceDTO:
    channel: str
    enabled: bool

    @staticmethod
    def from_entity(preference: ChannelPreference) -> "ChannelPreferenceDTO":
        return ChannelPreferenceDTO(channel=preference.canal.value, enabled=preference.habilitado)
