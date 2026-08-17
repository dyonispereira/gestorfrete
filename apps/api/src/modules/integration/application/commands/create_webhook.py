from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.integration.application.dtos.webhook_dto import WebhookCreatedDTO, WebhookDTO
from modules.integration.domain.entities.webhook import Webhook
from modules.integration.infrastructure.persistence.repositories.sqlalchemy_integration_config_repository import (
    SqlAlchemyIntegrationConfigRepository,
)
from modules.integration.infrastructure.persistence.repositories.sqlalchemy_webhook_repository import (
    SqlAlchemyWebhookRepository,
)
from modules.storage.domain.entities.file import File
from modules.storage.domain.value_objects.file_origin import FileOrigin
from modules.storage.infrastructure.object_storage import build_storage_key, ensure_bucket_exists, upload_object_bytes
from modules.storage.infrastructure.persistence.repositories.sqlalchemy_file_repository import (
    SqlAlchemyFileRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateWebhookCommand(Command):
    actor: AuthenticatedActor
    integration_config_id: uuid.UUID | None
    target_url: str
    subscribed_events: list[str]


class CreateWebhookHandler(CommandHandler[CreateWebhookCommand, WebhookCreatedDTO]):
    """`signing_secret` é gerado aqui, nunca aceito no corpo — devolvido só nesta resposta (D084-
    style). Persistido como `File` `GERADO_PELO_SISTEMA` (cofre de segredo, `storage`), nunca lido
    de volta por nenhum endpoint."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateWebhookCommand) -> WebhookCreatedDTO:
        await ensure_bucket_exists()

        async with SQLAlchemyUnitOfWork() as uow:
            if command.integration_config_id is not None:
                config_repo = SqlAlchemyIntegrationConfigRepository(uow.session)
                if await config_repo.get_by_id(command.integration_config_id) is None:
                    raise NotFoundError(
                        "INTEGRATION_CONFIG_NOT_FOUND", "Configuração de Integração não encontrada."
                    )

            signing_secret = secrets.token_hex(32)
            now = datetime.now(timezone.utc)

            secret_file = File.declare(
                nome_original="webhook-signing-secret", tipo_mime="text/plain", tamanho_bytes=len(signing_secret),
                origem=FileOrigin.GERADO_PELO_SISTEMA, storage_key="", versao=1, arquivo_anterior_id=None, now=now,
                created_by=command.actor.user_id,
            )
            secret_file.storage_key = build_storage_key(command.actor.tenant_id, secret_file.id)
            secret_file.confirm(tamanho_bytes=len(signing_secret), hash_sha256=hashlib.sha256(signing_secret.encode()).hexdigest())
            await SqlAlchemyFileRepository(uow.session).add(secret_file)

            webhook = Webhook.create(
                configuracao_integracao_id=command.integration_config_id, url_destino=command.target_url,
                eventos_assinados=command.subscribed_events, segredo_hmac_arquivo_id=secret_file.id,
            )
            await SqlAlchemyWebhookRepository(uow.session).add(webhook)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="webhooks", entidade_id=webhook.id,
                acao="CRIACAO", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"target_url": command.target_url},
            )
            await uow.commit()

        await upload_object_bytes(secret_file.storage_key, signing_secret.encode(), "text/plain")

        return WebhookCreatedDTO(webhook=WebhookDTO.from_entity(webhook), signing_secret=signing_secret)
