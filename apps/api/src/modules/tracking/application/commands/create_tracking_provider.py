from __future__ import annotations

from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError
from modules.tracking.application.dtos.tracking_provider_dto import TrackingProviderDTO
from modules.tracking.domain.entities.tracking_provider import TrackingProvider
from modules.tracking.infrastructure.persistence.repositories.sqlalchemy_tracking_provider_repository import (
    SqlAlchemyTrackingProviderRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateTrackingProviderCommand(Command):
    actor: AuthenticatedActor
    name: str


class CreateTrackingProviderHandler(CommandHandler[CreateTrackingProviderCommand, TrackingProviderDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateTrackingProviderCommand) -> TrackingProviderDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyTrackingProviderRepository(uow.session)
            if await repo.get_by_nome(command.name) is not None:
                raise ConflictError("TRACKING_PROVIDER_NAME_ALREADY_EXISTS", "Já existe um provedor com esse nome.")

            provider = TrackingProvider.create(nome=command.name)
            await repo.add(provider)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="provedores_rastreamento",
                entidade_id=provider.id, acao="CRIACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id), dados_depois={"nome": provider.nome},
            )
            await uow.commit()

        return TrackingProviderDTO.from_entity(provider)
