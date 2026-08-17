from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.ai.application.dtos.ai_anomaly_dto import AIAnomalyDTO
from modules.ai.domain.value_objects.anomaly_status import AnomalyStatus
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_ai_anomaly_repository import (
    SqlAlchemyAIAnomalyRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ReviewAnomalyCommand(Command):
    actor: AuthenticatedActor
    anomaly_id: uuid.UUID
    resolution: AnomalyStatus
    notes: str | None


class ReviewAnomalyHandler(CommandHandler[ReviewAnomalyCommand, AIAnomalyDTO]):
    """`075` — única transição real: `ABERTA → INVESTIGADA` ou `ABERTA → DESCARTADA`."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: ReviewAnomalyCommand) -> AIAnomalyDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyAIAnomalyRepository(uow.session)
            anomaly = await repo.get_by_id(command.anomaly_id)
            if anomaly is None:
                raise NotFoundError("AI_ANOMALY_NOT_FOUND", "Anomalia Detectada não encontrada.")

            anomaly.review(resolution=command.resolution)
            await repo.add(anomaly)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="anomalias_detectadas",
                entidade_id=anomaly.id, acao="ALTERACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"status": command.resolution.value, "notes": command.notes},
            )
            await uow.commit()

        return AIAnomalyDTO.from_entity(anomaly)
