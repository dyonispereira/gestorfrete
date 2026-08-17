from __future__ import annotations

from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError
from modules.ai.application.dtos.ai_model_dto import AIModelDTO
from modules.ai.domain.entities.ai_model import AIModel
from modules.ai.domain.value_objects.logical_provider import LogicalProvider
from modules.ai.domain.value_objects.model_type import ModelType
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_model_repository import (
    SqlAlchemyAIModelRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateAIModelCommand(Command):
    actor: AuthenticatedActor
    name: str
    type: ModelType
    version: str
    logical_provider: LogicalProvider
    capability: str
    max_context: int | None


class CreateAIModelHandler(CommandHandler[CreateAIModelCommand, AIModelDTO]):
    """`071` — D170/D309: `logical_provider` é sempre o conceito lógico, nunca o nome de um
    provedor real. "Nova versão" de um Modelo é simplesmente um novo `POST` com o mesmo `name` e
    `version` diferente — `uq_modelos_ia_nome_versao` impede duplicidade."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateAIModelCommand) -> AIModelDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyAIModelRepository(uow.session)

            if await repo.exists_with_name_and_version(command.name, command.version):
                raise ConflictError(
                    "AI_MODEL_NAME_VERSION_ALREADY_EXISTS", "Já existe um Modelo de IA com esse nome e versão."
                )

            model = AIModel.create(
                tenant_id=command.actor.tenant_id, nome=command.name, tipo=command.type, versao=command.version,
                fornecedor_logico=command.logical_provider, capacidade=command.capability,
                contexto_maximo=command.max_context,
            )
            await repo.add(model)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="modelos_ia", entidade_id=model.id,
                acao="CRIACAO", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"name": command.name, "version": command.version},
            )
            await uow.commit()

        return AIModelDTO.from_entity(model)
