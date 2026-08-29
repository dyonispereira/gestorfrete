from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from modules.maintenance.application.dtos.ordem_servico_dto import OrdemServicoDTO
from modules.maintenance.domain.entities.ordem_servico import OrdemServico
from modules.maintenance.domain.entities.ordem_servico_status_history_entry import OrdemServicoStatusHistoryEntry
from modules.maintenance.domain.value_objects.ordem_servico_origem_abertura import OrdemServicoOrigemAbertura
from modules.maintenance.domain.value_objects.ordem_servico_tipo import OrdemServicoTipo
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_ordem_servico_repository import (
    SqlAlchemyOrdemServicoRepository,
)
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_ordem_servico_status_history_repository import (
    SqlAlchemyOrdemServicoStatusHistoryRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateOrdemServicoCommand(Command):
    actor: AuthenticatedActor
    veiculo_tracionador_id: uuid.UUID
    tipo: str
    descricao_problema: str
    composicao_veicular_id: uuid.UUID | None = None
    fornecedor_executor_id: uuid.UUID | None = None
    origem_abertura: str = "MANUAL"


class CreateOrdemServicoHandler(CommandHandler[CreateOrdemServicoCommand, OrdemServicoDTO]):
    """Nasce `ABERTA`. `origem_abertura` default `MANUAL` — o valor `CHECKLIST_REPROVADO` é usado
    só pelo gatilho automático em `reject_checklist.py`, nunca escolhido livremente pelo usuário."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateOrdemServicoCommand) -> OrdemServicoDTO:
        now = datetime.now(timezone.utc)
        async with SQLAlchemyUnitOfWork() as uow:
            os_repo = SqlAlchemyOrdemServicoRepository(uow.session)
            history_repo = SqlAlchemyOrdemServicoStatusHistoryRepository(uow.session)

            ordem_servico = OrdemServico.create(
                veiculo_tracionador_id=command.veiculo_tracionador_id,
                composicao_veicular_id=command.composicao_veicular_id,
                fornecedor_executor_id=command.fornecedor_executor_id, tipo=OrdemServicoTipo(command.tipo),
                origem_abertura=OrdemServicoOrigemAbertura(command.origem_abertura),
                descricao_problema=command.descricao_problema, criado_por=command.actor.user_id, now=now,
            )
            await os_repo.add(ordem_servico)
            await history_repo.add(
                OrdemServicoStatusHistoryEntry.create(
                    ordem_servico_id=ordem_servico.id, status=ordem_servico.status.value,
                    usuario_id=command.actor.user_id, origem="usuario", now=now,
                )
            )
            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="ordens_servico",
                entidade_id=ordem_servico.id, acao="CRIACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"tipo": ordem_servico.tipo.value, "veiculo_tracionador_id": str(command.veiculo_tracionador_id)},
            )
            await uow.commit()

        return OrdemServicoDTO.from_entity(ordem_servico)
