from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.ai.application.dtos.computer_vision_reading_dto import ComputerVisionReadingDTO
from modules.ai.infrastructure.persistence.repositories.sqlalchemy_computer_vision_reading_repository import (
    SqlAlchemyComputerVisionReadingRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class RejectComputerVisionReadingCommand(Command):
    actor: AuthenticatedActor
    reading_id: uuid.UUID
    reason: str


class RejectComputerVisionReadingHandler(
    CommandHandler[RejectComputerVisionReadingCommand, ComputerVisionReadingDTO]
):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: RejectComputerVisionReadingCommand) -> ComputerVisionReadingDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyComputerVisionReadingRepository(uow.session)
            reading = await repo.get_by_id(command.reading_id)
            if reading is None:
                raise NotFoundError("AI_CV_READING_NOT_FOUND", "Leitura por Visão Computacional não encontrada.")

            reading.reject(usuario_id=command.actor.user_id)
            await repo.add(reading)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="leituras_visao_computacional",
                entidade_id=reading.id, acao="ALTERACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"status": "REJEITADA", "reason": command.reason},
            )
            await uow.commit()

        return ComputerVisionReadingDTO.from_entity(reading)
