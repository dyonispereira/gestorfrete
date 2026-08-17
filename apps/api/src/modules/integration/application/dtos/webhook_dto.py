from __future__ import annotations

import uuid
from dataclasses import dataclass

from modules.integration.domain.entities.webhook import Webhook


@dataclass(frozen=True)
class WebhookDTO:
    id: uuid.UUID
    integration_config_id: uuid.UUID | None
    target_url: str
    subscribed_events: list[str]
    status: str

    @staticmethod
    def from_entity(webhook: Webhook) -> "WebhookDTO":
        return WebhookDTO(
            id=webhook.id, integration_config_id=webhook.configuracao_integracao_id,
            target_url=webhook.url_destino, subscribed_events=list(webhook.eventos_assinados),
            status=webhook.status.value,
        )


@dataclass(frozen=True)
class WebhookCreatedDTO:
    webhook: WebhookDTO
    signing_secret: str
