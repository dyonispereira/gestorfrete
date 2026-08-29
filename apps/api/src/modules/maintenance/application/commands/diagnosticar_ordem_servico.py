from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.maintenance.application.dtos.ordem_servico_dto import OrdemServicoDTO
from modules.maintenance.domain.entities.ordem_servico_status_history_entry import OrdemServicoStatusHistoryEntry
from modules.maintenance.domain.value_objects.ordem_servico_causa import OrdemServicoCausa
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_ordem_servico_repository import (
    SqlAlchemyOrdemServicoRepository,
)
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_ordem_servico_status_history_repository import (
    SqlAlchemyOrdemServicoStatusHistoryRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class DiagnosticarOrdemServicoCommand(Command):
    actor: AuthenticatedActor
    ordem_servico_id: uuid.UUID
    diagnostico_tecnico: str | None = None
    causa: str | None = None
    causa_raiz: str | None = None
    mecanico_id: uuid.UUID | None = None
    necessita_aprovacao: bool = False


class DiagnosticarOrdemServicoHandler(CommandHandler[DiagnosticarOrdemServicoCommand, OrdemServicoDTO]):
    """`ABERTA→EM_DIAGNOSTICO`. `necessita_aprovacao` é informado explicitamente aqui — a alçada de
    aprovação configurável por tenant ainda não existe (`settings`, ver plano), então não é
    calculada automaticamente."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: DiagnosticarOrdemServicoCommand) -> OrdemServicoDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            os_repo = SqlAlchemyOrdemServicoRepository(uow.session)
            history_repo = SqlAlchemyOrdemServicoStatusHistoryRepository(uow.session)

            ordem_servico = await os_repo.get_by_id(command.ordem_servico_id)
            if ordem_servico is None:
                raise NotFoundError("MAINTENANCE_WORK_ORDER_NOT_FOUND", "Ordem de Serviço não encontrada.")

            now = datetime.now(timezone.utc)
            ordem_servico.diagnosticar(
                causa=OrdemServicoCausa(command.causa) if command.causa else None, causa_raiz=command.causa_raiz,
                diagnostico_tecnico=command.diagnostico_tecnico, mecanico_id=command.mecanico_id,
                necessita_aprovacao=command.necessita_aprovacao, now=now, atualizado_por=command.actor.user_id,
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
                entidade_id=ordem_servico.id, acao="TRANSICAO_STATUS", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id), dados_depois={"status": ordem_servico.status.value},
            )
            await uow.commit()

        return OrdemServicoDTO.from_entity(ordem_servico)
