from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.documents.application.dtos.referenced_nfe_dto import ReferencedNfeDTO
from modules.documents.domain.entities.referenced_nfe import ReferencedNfe
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_cte_repository import (
    SqlAlchemyCteRepository,
)
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_referenced_nfe_repository import (
    SqlAlchemyReferencedNfeRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateReferencedNfeCommand(Command):
    actor: AuthenticatedActor
    cte_id: uuid.UUID
    access_key: str


class CreateReferencedNfeHandler(CommandHandler[CreateReferencedNfeCommand, ReferencedNfeDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateReferencedNfeCommand) -> ReferencedNfeDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            cte_repo = SqlAlchemyCteRepository(uow.session)
            nfe_repo = SqlAlchemyReferencedNfeRepository(uow.session)

            cte = await cte_repo.get_by_id(command.cte_id)
            if cte is None:
                raise NotFoundError("FISCAL_CTE_NOT_FOUND", "CT-e não encontrado.")

            nfe = ReferencedNfe.create(cte_id=cte.id, chave_acesso=command.access_key)
            await nfe_repo.add(nfe)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="nfe_referenciadas",
                entidade_id=nfe.id, acao="CRIACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id), dados_depois={"cte_id": str(cte.id)},
            )
            await uow.commit()

        return ReferencedNfeDTO.from_entity(nfe)
