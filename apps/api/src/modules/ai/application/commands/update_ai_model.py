from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.ai.application.dtos.ai_model_dto import AIModelDTO
from modules.ai.domain.value_objects.model_status import ModelStatus
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_model_repository import (
    SqlAlchemyAIModelRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateAIModelCommand(Command):
    actor: AuthenticatedActor
    model_id: uuid.UUID
    capability: str | None
    max_context: int | None
    status: ModelStatus | None


class UpdateAIModelHandler(CommandHandler[UpdateAIModelCommand, AIModelDTO]):
    """`071` — D229 parcial: só `capability`/`max_context`/`status`. `name`/`type`/`version`/
    `logical_provider` nunca editáveis (identidade do modelo)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: UpdateAIModelCommand) -> AIModelDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyAIModelRepository(uow.session)
            model = await repo.get_by_id(command.model_id)
            if model is None:
                raise NotFoundError("AI_MODEL_NOT_FOUND", "Modelo de IA não encontrado.")

            model.update_fields(capacidade=command.capability, contexto_maximo=command.max_context, status=command.status)
            await repo.add(model)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="modelos_ia",
                entidade_id=model.id, acao="ALTERACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )
            await uow.commit()

        return AIModelDTO.from_entity(model)
