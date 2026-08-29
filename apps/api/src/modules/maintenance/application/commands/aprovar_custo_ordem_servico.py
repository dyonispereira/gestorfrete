from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.maintenance.application.dtos.ordem_servico_dto import OrdemServicoDTO
from modules.maintenance.domain.entities.aprovacao_custo import AprovacaoCusto
from modules.maintenance.domain.entities.ordem_servico_status_history_entry import OrdemServicoStatusHistoryEntry
from modules.maintenance.domain.value_objects.aprovacao_custo_decisao import AprovacaoCustoDecisao
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_aprovacao_custo_repository import (
    SqlAlchemyAprovacaoCustoRepository,
)
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_ordem_servico_repository import (
    SqlAlchemyOrdemServicoRepository,
)
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_ordem_servico_status_history_repository import (
    SqlAlchemyOrdemServicoStatusHistoryRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class AprovarCustoOrdemServicoCommand(Command):
    actor: AuthenticatedActor
    ordem_servico_id: uuid.UUID
    justificativa: str | None = None


class AprovarCustoOrdemServicoHandler(CommandHandler[AprovarCustoOrdemServicoCommand, OrdemServicoDTO]):
    """`AGUARDANDO_APROVACAO→EM_EXECUCAO`, registrando uma `AprovacaoCusto` (nível 1)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: AprovarCustoOrdemServicoCommand) -> OrdemServicoDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            os_repo = SqlAlchemyOrdemServicoRepository(uow.session)
            history_repo = SqlAlchemyOrdemServicoStatusHistoryRepository(uow.session)
            aprovacao_repo = SqlAlchemyAprovacaoCustoRepository(uow.session)

            ordem_servico = await os_repo.get_by_id(command.ordem_servico_id)
            if ordem_servico is None:
                raise NotFoundError("MAINTENANCE_WORK_ORDER_NOT_FOUND", "Ordem de Serviço não encontrada.")

            now = datetime.now(timezone.utc)
            ordem_servico.aprovar_custo(now=now, atualizado_por=command.actor.user_id)
            await os_repo.add(ordem_servico)

            await aprovacao_repo.add(
                AprovacaoCusto.create(
                    ordem_servico_id=ordem_servico.id, decisao=AprovacaoCustoDecisao.APROVADO,
                    justificativa=command.justificativa, ator_id=command.actor.user_id, now=now,
                )
            )
            await history_repo.add(
                OrdemServicoStatusHistoryEntry.create(
                    ordem_servico_id=ordem_servico.id, status=ordem_servico.status.value,
                    usuario_id=command.actor.user_id, origem="usuario", now=now,
                )
            )
            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="ordens_servico",
                entidade_id=ordem_servico.id, acao="TRANSICAO_STATUS", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id), dados_depois={"status": ordem_servico.status.value},
            )
            await uow.commit()

        return OrdemServicoDTO.from_entity(ordem_servico)
