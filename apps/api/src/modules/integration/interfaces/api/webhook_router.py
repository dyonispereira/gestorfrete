from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.integration.application.commands.create_webhook import CreateWebhookCommand, CreateWebhookHandler
from modules.integration.application.commands.set_webhook_status import (
    ActivateWebhookCommand,
    ActivateWebhookHandler,
    SuspendWebhookCommand,
    SuspendWebhookHandler,
)
from modules.integration.application.commands.test_webhook import TestWebhookCommand, TestWebhookHandler
from modules.integration.application.commands.update_webhook import UpdateWebhookCommand, UpdateWebhookHandler
from modules.integration.application.queries.get_webhook import GetWebhookHandler, GetWebhookQuery
from modules.integration.application.queries.list_webhooks import ListWebhooksHandler, ListWebhooksQuery
from modules.integration.interfaces.schemas.webhook_schemas import (
    CreateWebhookRequest,
    TestWebhookResponse,
    UpdateWebhookRequest,
    WebhookResponse,
)
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/integrations/webhooks", tags=["Webhooks"])


@router.get("")
async def list_webhooks(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    integration_config_id: uuid.UUID | None = None,
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("integration.webhook.view")),
) -> dict[str, Any]:
    handler = ListWebhooksHandler(get_session_factory())
    result = await handler.handle(
        ListWebhooksQuery(
            actor=actor, page=page, limit=limit, integration_config_id=integration_config_id, status=status
        )
    )
    return {
        "data": [WebhookResponse.from_dto(w) for w in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("integration.webhook.view"))
) -> WebhookResponse:
    handler = GetWebhookHandler(get_session_factory())
    dto = await handler.handle(GetWebhookQuery(actor=actor, webhook_id=webhook_id))
    return WebhookResponse.from_dto(dto)


@router.post("", response_model=WebhookResponse, status_code=201)
async def create_webhook(
    body: CreateWebhookRequest, actor: AuthenticatedActor = Depends(require_permission("integration.webhook.create"))
) -> WebhookResponse:
    handler = CreateWebhookHandler()
    result = await handler.handle(
        CreateWebhookCommand(
            actor=actor, integration_config_id=body.integration_config_id, target_url=body.target_url,
            subscribed_events=body.subscribed_events,
        )
    )
    return WebhookResponse.from_created_dto(result)


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: uuid.UUID, body: UpdateWebhookRequest,
    actor: AuthenticatedActor = Depends(require_permission("integration.webhook.edit")),
) -> WebhookResponse:
    handler = UpdateWebhookHandler()
    dto = await handler.handle(
        UpdateWebhookCommand(
            actor=actor, webhook_id=webhook_id, target_url=body.target_url,
            subscribed_events=body.subscribed_events,
        )
    )
    return WebhookResponse.from_dto(dto)


@router.post("/{webhook_id}/commands/activate", response_model=WebhookResponse)
async def activate_webhook(
    webhook_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("integration.webhook.activate"))
) -> WebhookResponse:
    handler = ActivateWebhookHandler()
    dto = await handler.handle(ActivateWebhookCommand(actor=actor, webhook_id=webhook_id))
    return WebhookResponse.from_dto(dto)


@router.post("/{webhook_id}/commands/suspend", response_model=WebhookResponse)
async def suspend_webhook(
    webhook_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("integration.webhook.suspend"))
) -> WebhookResponse:
    handler = SuspendWebhookHandler()
    dto = await handler.handle(SuspendWebhookCommand(actor=actor, webhook_id=webhook_id))
    return WebhookResponse.from_dto(dto)


@router.post("/{webhook_id}/commands/test", response_model=TestWebhookResponse)
async def test_webhook(
    webhook_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("integration.webhook.test"))
) -> TestWebhookResponse:
    handler = TestWebhookHandler()
    result = await handler.handle(TestWebhookCommand(actor=actor, webhook_id=webhook_id))
    return TestWebhookResponse(delivered=result.delivered, http_status=result.http_status, duration_ms=result.duration_ms)
