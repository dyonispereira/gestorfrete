from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from modules.notification_center.application.dtos.notification_dto import ChannelPreferenceDTO, NotificationDTO


class NotificationResponse(BaseModel):
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
    def from_dto(dto: NotificationDTO) -> "NotificationResponse":
        return NotificationResponse(
            id=dto.id, channel=dto.channel, origin_event_type=dto.origin_event_type, entity_type=dto.entity_type,
            entity_id=dto.entity_id, title=dto.title, message=dto.message, status=dto.status, sent_at=dto.sent_at,
            read_at=dto.read_at,
        )


class ChannelPreferenceResponse(BaseModel):
    channel: str
    enabled: bool

    @staticmethod
    def from_dto(dto: ChannelPreferenceDTO) -> "ChannelPreferenceResponse":
        return ChannelPreferenceResponse(channel=dto.channel, enabled=dto.enabled)


class UpdateChannelPreferenceRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    enabled: bool
