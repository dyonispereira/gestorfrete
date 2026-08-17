from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.notification_center.application.commands.mark_notification_read import (
    MarkNotificationReadCommand,
    MarkNotificationReadHandler,
)
from modules.notification_center.application.commands.update_channel_preference import (
    UpdateChannelPreferenceCommand,
    UpdateChannelPreferenceHandler,
)
from modules.notification_center.application.queries.get_notification import GetNotificationHandler, GetNotificationQuery
from modules.notification_center.application.queries.list_channel_preferences import (
    ListChannelPreferencesHandler,
    ListChannelPreferencesQuery,
)
from modules.notification_center.application.queries.list_notifications import (
    ListNotificationsHandler,
    ListNotificationsQuery,
)
from modules.notification_center.domain.value_objects.notification_channel import NotificationChannel
from modules.notification_center.interfaces.schemas.notification_schemas import (
    ChannelPreferenceResponse,
    NotificationResponse,
    UpdateChannelPreferenceRequest,
)
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
async def list_notifications(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    channel: str | None = None,
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("notification_center.alert.view")),
) -> dict[str, Any]:
    handler = ListNotificationsHandler(get_session_factory())
    result = await handler.handle(
        ListNotificationsQuery(actor=actor, page=page, limit=limit, channel=channel, status=status)
    )
    return {
        "data": [NotificationResponse.from_dto(n) for n in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/channel-preferences")
async def list_channel_preferences(
    actor: AuthenticatedActor = Depends(require_permission("notification_center.channel_preference.view")),
) -> dict[str, Any]:
    handler = ListChannelPreferencesHandler(get_session_factory())
    items = await handler.handle(ListChannelPreferencesQuery(actor=actor))
    return {"data": [ChannelPreferenceResponse.from_dto(p) for p in items]}


@router.patch("/channel-preferences/{channel}", response_model=ChannelPreferenceResponse)
async def update_channel_preference(
    channel: str, body: UpdateChannelPreferenceRequest,
    actor: AuthenticatedActor = Depends(require_permission("notification_center.channel_preference.edit")),
) -> ChannelPreferenceResponse:
    handler = UpdateChannelPreferenceHandler()
    dto = await handler.handle(
        UpdateChannelPreferenceCommand(actor=actor, channel=NotificationChannel(channel), enabled=body.enabled)
    )
    return ChannelPreferenceResponse.from_dto(dto)


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("notification_center.alert.view")),
) -> NotificationResponse:
    handler = GetNotificationHandler(get_session_factory())
    dto = await handler.handle(GetNotificationQuery(actor=actor, notification_id=notification_id))
    return NotificationResponse.from_dto(dto)


@router.post("/{notification_id}/commands/mark-read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("notification_center.alert.manage_own")),
) -> NotificationResponse:
    handler = MarkNotificationReadHandler()
    dto = await handler.handle(MarkNotificationReadCommand(actor=actor, notification_id=notification_id))
    return NotificationResponse.from_dto(dto)
