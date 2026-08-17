from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict

from modules.integration.application.dtos.webhook_dto import WebhookCreatedDTO, WebhookDTO


class CreateWebhookRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    integration_config_id: uuid.UUID | None = None
    target_url: str
    subscribed_events: list[str]


class UpdateWebhookRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    target_url: str | None = None
    subscribed_events: list[str] | None = None


class WebhookResponse(BaseModel):
    """Sem `audit` — `webhooks` não tem nenhuma coluna de timestamp na DDL congelada (D400-family)."""

    id: uuid.UUID
    integration_config_id: uuid.UUID | None
    target_url: str
    subscribed_events: list[str]
    signing_secret: str | None = None
    status: str

    @staticmethod
    def from_dto(dto: WebhookDTO, *, signing_secret: str | None = None) -> "WebhookResponse":
        return WebhookResponse(
            id=dto.id, integration_config_id=dto.integration_config_id, target_url=dto.target_url,
            subscribed_events=dto.subscribed_events, signing_secret=signing_secret, status=dto.status,
        )

    @staticmethod
    def from_created_dto(dto: WebhookCreatedDTO) -> "WebhookResponse":
        return WebhookResponse.from_dto(dto.webhook, signing_secret=dto.signing_secret)


class TestWebhookResponse(BaseModel):
    delivered: bool
    http_status: int | None
    duration_ms: int
