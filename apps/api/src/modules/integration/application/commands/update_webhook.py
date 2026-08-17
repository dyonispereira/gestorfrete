from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.integration.application.dtos.webhook_dto import WebhookDTO
from modules.integration.infrastructure.persistence.repositories.sqlalchemy_webhook_repository import (
    SqlAlchemyWebhookRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateWebhookCommand(Command):
    actor: AuthenticatedActor
    webhook_id: uuid.UUID
    target_url: str | None
    subscribed_events: list[str] | None


class UpdateWebhookHandler(CommandHandler[UpdateWebhookCommand, WebhookDTO]):
    """D229 — parcial (`target_url`/`subscribed_events`). Nunca reemite `signing_secret`."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: UpdateWebhookCommand) -> WebhookDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyWebhookRepository(uow.session)
            webhook = await repo.get_by_id(command.webhook_id)
            if webhook is None:
                raise NotFoundError("INTEGRATION_WEBHOOK_NOT_FOUND", "Webhook não encontrado.")

            webhook.update(url_destino=command.target_url, eventos_assinados=command.subscribed_events)
            await repo.add(webhook)
            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="webhooks",
                entidade_id=webhook.id, acao="ALTERACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )
            await uow.commit()

        return WebhookDTO.from_entity(webhook)
