from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.ai.application.dtos.ai_suggestion_dto import AISuggestionDTO
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_suggestion_repository import (
    SqlAlchemyAISuggestionRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class AcceptSuggestionCommand(Command):
    actor: AuthenticatedActor
    suggestion_id: uuid.UUID


class AcceptSuggestionHandler(CommandHandler[AcceptSuggestionCommand, AISuggestionDTO]):
    """`073`/D311 — só registra a decisão (`status=ACEITA`, `decision_user_id`, `decided_at`).
    Executar a ação sugerida é sempre uma chamada separada e explícita ao comando do bounded
    context operacional responsável — nunca feita por este Handler."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: AcceptSuggestionCommand) -> AISuggestionDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyAISuggestionRepository(uow.session)
            suggestion = await repo.get_by_id(command.suggestion_id)
            if suggestion is None:
                raise NotFoundError("AI_SUGGESTION_NOT_FOUND", "Sugestão de IA não encontrada.")

            suggestion.accept(usuario_id=command.actor.user_id, now=datetime.now(timezone.utc))
            await repo.add(suggestion)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="sugestoes_ia",
                entidade_id=suggestion.id, acao="ALTERACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id), dados_depois={"status": "ACEITA"},
            )
            await uow.commit()

        return AISuggestionDTO.from_entity(suggestion)
