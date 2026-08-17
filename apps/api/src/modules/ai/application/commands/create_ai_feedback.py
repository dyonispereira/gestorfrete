from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.ai.application.dtos.ai_feedback_dto import AIFeedbackDTO
from modules.ai.domain.entities.ai_feedback import AIFeedback
from modules.ai.domain.value_objects.feedback_output_type import FeedbackOutputType
from modules.ai.domain.value_objects.feedback_result import FeedbackResult
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_anomaly_repository import (
    SqlAlchemyAIAnomalyRepository,
)
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_classification_repository import (
    SqlAlchemyAIClassificationRepository,
)
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_feedback_repository import (
    SqlAlchemyAIFeedbackRepository,
)
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_prediction_repository import (
    SqlAlchemyAIPredictionRepository,
)
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_suggestion_repository import (
    SqlAlchemyAISuggestionRepository,
)
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_computer_vision_reading_repository import (
    SqlAlchemyComputerVisionReadingRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor

_NOT_FOUND_CODE_BY_TYPE = {
    FeedbackOutputType.SUGESTAO: "AI_SUGGESTION_NOT_FOUND",
    FeedbackOutputType.PREDICAO: "AI_PREDICTION_NOT_FOUND",
    FeedbackOutputType.CLASSIFICACAO: "AI_CLASSIFICATION_NOT_FOUND",
    FeedbackOutputType.ANOMALIA: "AI_ANOMALY_NOT_FOUND",
    FeedbackOutputType.LEITURA_VISAO_COMPUTACIONAL: "AI_CV_READING_NOT_FOUND",
}


@dataclass(frozen=True)
class CreateAIFeedbackCommand(Command):
    actor: AuthenticatedActor
    output_type: FeedbackOutputType
    output_id: uuid.UUID
    result: FeedbackResult
    justification: str | None
    actual_result: str | None


class CreateAIFeedbackHandler(CommandHandler[CreateAIFeedbackCommand, AIFeedbackDTO]):
    """`077`/D165 — Feedback nunca reabre/altera a saída de IA avaliada nem a Inferência original;
    é sempre um registro independente. `output_id` é validado contra o repositório correspondente
    ao `output_type` (polimórfico sobre as 5 saídas, `404` se não existir)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateAIFeedbackCommand) -> AIFeedbackDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            output_exists = await self._output_exists(uow, command.output_type, command.output_id)
            if not output_exists:
                raise NotFoundError(
                    _NOT_FOUND_CODE_BY_TYPE[command.output_type], "Saída de IA referenciada não encontrada."
                )

            repo = SqlAlchemyAIFeedbackRepository(uow.session)
            feedback = AIFeedback.create(
                tenant_id=command.actor.tenant_id, saida_ia_tipo=command.output_type,
                saida_ia_id=command.output_id, usuario_id=command.actor.user_id, resultado=command.result,
                justificativa=command.justification, resultado_real=command.actual_result,
                now=datetime.now(timezone.utc),
            )
            await repo.add(feedback)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="feedbacks_ia",
                entidade_id=feedback.id, acao="CRIACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"output_type": command.output_type.value, "result": command.result.value},
            )
            await uow.commit()

        return AIFeedbackDTO.from_entity(feedback)

    @staticmethod
    async def _output_exists(uow: SQLAlchemyUnitOfWork, output_type: FeedbackOutputType, output_id: uuid.UUID) -> bool:
        if output_type == FeedbackOutputType.SUGESTAO:
            return await SqlAlchemyAISuggestionRepository(uow.session).get_by_id(output_id) is not None
        if output_type == FeedbackOutputType.PREDICAO:
            return await SqlAlchemyAIPredictionRepository(uow.session).get_by_id(output_id) is not None
        if output_type == FeedbackOutputType.CLASSIFICACAO:
            return await SqlAlchemyAIClassificationRepository(uow.session).get_by_id(output_id) is not None
        if output_type == FeedbackOutputType.ANOMALIA:
            return await SqlAlchemyAIAnomalyRepository(uow.session).get_by_id(output_id) is not None
        return await SqlAlchemyComputerVisionReadingRepository(uow.session).get_by_id(output_id) is not None
