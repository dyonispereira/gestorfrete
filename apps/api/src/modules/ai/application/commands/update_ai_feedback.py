from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.ai.application.dtos.ai_feedback_dto import AIFeedbackDTO
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_feedback_repository import (
    SqlAlchemyAIFeedbackRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateAIFeedbackCommand(Command):
    actor: AuthenticatedActor
    feedback_id: uuid.UUID
    actual_result: str


class UpdateAIFeedbackHandler(CommandHandler[UpdateAIFeedbackCommand, AIFeedbackDTO]):
    """`077` — único campo editável: `actual_result` (D192, observação tardia). `result`/
    `justification` permanecem imutáveis — D165, Feedback nunca reabre a decisão original."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: UpdateAIFeedbackCommand) -> AIFeedbackDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyAIFeedbackRepository(uow.session)
            feedback = await repo.get_by_id(command.feedback_id)
            if feedback is None:
                raise NotFoundError("AI_FEEDBACK_NOT_FOUND", "Feedback de IA não encontrado.")

            feedback.record_actual_result(resultado_real=command.actual_result)
            await repo.add(feedback)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="feedbacks_ia",
                entidade_id=feedback.id, acao="ALTERACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )
            await uow.commit()

        return AIFeedbackDTO.from_entity(feedback)
