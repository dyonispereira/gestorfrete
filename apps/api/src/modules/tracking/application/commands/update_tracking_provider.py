from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.tracking.application.dtos.tracking_provider_dto import TrackingProviderDTO
from modules.tracking.domain.value_objects.tracking_provider_status import TrackingProviderStatus
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_tracking_provider_repository import (
    SqlAlchemyTrackingProviderRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateTrackingProviderCommand(Command):
    actor: AuthenticatedActor
    provider_id: uuid.UUID
    name: str | None
    status: TrackingProviderStatus | None


class UpdateTrackingProviderHandler(CommandHandler[UpdateTrackingProviderCommand, TrackingProviderDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: UpdateTrackingProviderCommand) -> TrackingProviderDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyTrackingProviderRepository(uow.session)
            provider = await repo.get_by_id(command.provider_id)
            if provider is None:
                raise NotFoundError("TRACKING_PROVIDER_NOT_FOUND", "Provedor de Rastreamento não encontrado.")

            provider.update(nome=command.name, status=command.status)
            await repo.add(provider)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="provedores_rastreamento",
                entidade_id=provider.id, acao="ALTERACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )
            await uow.commit()

        return TrackingProviderDTO.from_entity(provider)
