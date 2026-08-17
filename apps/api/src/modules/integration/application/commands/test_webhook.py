from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

import httpx

from core.database.session import get_session_factory
from core.exceptions.base import NotFoundError
from modules.integration.infrastructure.persistence.repositories.sqlalchemy_webhook_repository import (
    SqlAlchemyWebhookRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor

_TEST_TIMEOUT_SECONDS = 5.0


@dataclass(frozen=True)
class TestWebhookCommand(Command):
    actor: AuthenticatedActor
    webhook_id: uuid.UUID


@dataclass(frozen=True)
class TestWebhookResultDTO:
    delivered: bool
    http_status: int | None
    duration_ms: int


class TestWebhookHandler(CommandHandler[TestWebhookCommand, TestWebhookResultDTO]):
    """`commands/test` — único lugar deste lote que sai para a rede de verdade, de forma síncrona
    (o próprio contrato define assim); payload sintético, nunca um evento de domínio real."""

    async def handle(self, command: TestWebhookCommand) -> TestWebhookResultDTO:
        session_factory = get_session_factory()
        async with session_factory() as session:
            repo = SqlAlchemyWebhookRepository(session)
            webhook = await repo.get_by_id(command.webhook_id)
        if webhook is None:
            raise NotFoundError("INTEGRATION_WEBHOOK_NOT_FOUND", "Webhook não encontrado.")

        payload = {"event": "webhook.test", "webhook_id": str(webhook.id)}
        started = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=_TEST_TIMEOUT_SECONDS) as client:
                response = await client.post(webhook.url_destino, json=payload)
            duration_ms = int((time.monotonic() - started) * 1000)
            return TestWebhookResultDTO(
                delivered=response.is_success, http_status=response.status_code, duration_ms=duration_ms
            )
        except httpx.HTTPError:
            duration_ms = int((time.monotonic() - started) * 1000)
            return TestWebhookResultDTO(delivered=False, http_status=None, duration_ms=duration_ms)
