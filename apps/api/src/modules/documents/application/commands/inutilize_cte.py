from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.documents.application.dtos.cte_dto import CteDTO
from modules.documents.domain.entities.cte_status_history_entry import CteStatusHistoryEntry
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_cte_repository import (
    SqlAlchemyCteRepository,
)
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_cte_status_history_repository import (
    SqlAlchemyCteStatusHistoryRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class InutilizeCteCommand(Command):
    actor: AuthenticatedActor
    cte_id: uuid.UUID


class InutilizeCteHandler(CommandHandler[InutilizeCteCommand, CteDTO]):
    """`RASCUNHO`/`VALIDADO→INUTILIZADO` — número reservado nunca transmitido."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: InutilizeCteCommand) -> CteDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            cte_repo = SqlAlchemyCteRepository(uow.session)
            history_repo = SqlAlchemyCteStatusHistoryRepository(uow.session)

            cte = await cte_repo.get_by_id(command.cte_id)
            if cte is None:
                raise NotFoundError("FISCAL_CTE_NOT_FOUND", "CT-e não encontrado.")

            now = datetime.now(timezone.utc)
            cte.inutilize(now=now)
            await cte_repo.add(cte)

            await history_repo.add(
                CteStatusHistoryEntry.create(
                    cte_id=cte.id, status=cte.status.value, usuario_id=command.actor.user_id,
                    origem="usuario", now=now,
                )
            )
            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="ctes", entidade_id=cte.id,
                acao="TRANSICAO_STATUS", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"status": cte.status.value},
            )
            await uow.commit()

        return CteDTO.from_entity(cte)
