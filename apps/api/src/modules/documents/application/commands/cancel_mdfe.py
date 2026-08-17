from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError, ValidationError
from modules.documents.application.dtos.mdfe_dto import MdfeDTO
from modules.documents.domain.entities.mdfe_status_history_entry import MdfeStatusHistoryEntry
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_mdfe_repository import (
    SqlAlchemyMdfeRepository,
)
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_mdfe_status_history_repository import (
    SqlAlchemyMdfeStatusHistoryRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CancelMdfeCommand(Command):
    actor: AuthenticatedActor
    mdfe_id: uuid.UUID
    notes: str


class CancelMdfeHandler(CommandHandler[CancelMdfeCommand, MdfeDTO]):
    """`PENDENTE`/`AUTORIZADO→CANCELADO` — nunca a partir de `ENCERRADO`."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CancelMdfeCommand) -> MdfeDTO:
        if not command.notes or not command.notes.strip():
            raise ValidationError("FISCAL_MDFE_NOTES_REQUIRED", "notes é obrigatória para cancelar.")

        async with SQLAlchemyUnitOfWork() as uow:
            mdfe_repo = SqlAlchemyMdfeRepository(uow.session)
            history_repo = SqlAlchemyMdfeStatusHistoryRepository(uow.session)

            mdfe = await mdfe_repo.get_by_id(command.mdfe_id)
            if mdfe is None:
                raise NotFoundError("FISCAL_MDFE_NOT_FOUND", "MDF-e não encontrado.")

            now = datetime.now(timezone.utc)
            mdfe.cancel()
            await mdfe_repo.add(mdfe)
            cte_ids = await mdfe_repo.list_cte_ids(mdfe.id)

            await history_repo.add(
                MdfeStatusHistoryEntry.create(
                    mdfe_id=mdfe.id, status=mdfe.status.value, usuario_id=command.actor.user_id,
                    origem="usuario", now=now, observacao=command.notes,
                )
            )
            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="mdfes", entidade_id=mdfe.id,
                acao="TRANSICAO_STATUS", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"status": mdfe.status.value}, motivo=command.notes,
            )
            await uow.commit()

        return MdfeDTO.from_entity(mdfe, cte_ids=cte_ids)
