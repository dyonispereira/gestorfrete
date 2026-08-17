from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ValidationError
from modules.integration.application.dtos.job_execution_dto import JobExecutionDTO
from modules.integration.application.job_type_registry import JOB_TYPE_REGISTRY
from modules.integration.domain.entities.job_execution import JobExecution
from modules.integration.infrastructure.persistence.repositories.sqlalchemy_job_execution_repository import (
    SqlAlchemyJobExecutionRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class TriggerJobCommand(Command):
    actor: AuthenticatedActor
    job_type: str
    parameters: dict[str, Any] | None


class TriggerJobHandler(CommandHandler[TriggerJobCommand, JobExecutionDTO]):
    """D322 — `job_type` validado contra `JOB_TYPE_REGISTRY`, vocabulário fechado no sentido de
    nunca aceitar execução de código arbitrário. Só cria o registro e "enfileira" — execução real
    fica fora deste contrato (D413), simulada por `JobInternalTransitions`."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: TriggerJobCommand) -> JobExecutionDTO:
        if command.job_type not in JOB_TYPE_REGISTRY:
            raise ValidationError("JOB_TYPE_NOT_REGISTERED", f"job_type desconhecido: {command.job_type}")

        now = datetime.now(timezone.utc)
        execution = JobExecution.trigger(tenant_id=command.actor.tenant_id, tipo_job=command.job_type, now=now)

        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyJobExecutionRepository(uow.session)
            await repo.add(execution)
            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="execucoes_job",
                entidade_id=execution.id, acao="CRIACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id), dados_depois={"job_type": command.job_type},
            )
            await uow.commit()

        return JobExecutionDTO.from_entity(execution)
