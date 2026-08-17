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
class ConfirmComputerVisionReadingCommand(Command):
    actor: AuthenticatedActor
    reading_id: uuid.UUID


class ConfirmComputerVisionReadingHandler(
    CommandHandler[ConfirmComputerVisionReadingCommand, ComputerVisionReadingDTO]
):
    """`076` — `usuario_confirmacao_id` sempre capturado da sessão autenticada, nunca aceito no
    corpo (mesmo princípio de D295). Reforça `ck_leituras_visao_computacional_confirmacao_humana`
    (audit 4) — a Application recusa antes mesmo de chegar ao banco, mas a constraint física
    continua a segunda camada de defesa."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: ConfirmComputerVisionReadingCommand) -> ComputerVisionReadingDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyComputerVisionReadingRepository(uow.session)
            reading = await repo.get_by_id(command.reading_id)
            if reading is None:
                raise NotFoundError("AI_CV_READING_NOT_FOUND", "Leitura por Visão Computacional não encontrada.")

            reading.confirm(usuario_id=command.actor.user_id)
            await repo.add(reading)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="leituras_visao_computacional",
                entidade_id=reading.id, acao="ALTERACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id), dados_depois={"status": "CONFIRMADA"},
            )
            await uow.commit()

        return ComputerVisionReadingDTO.from_entity(reading)
