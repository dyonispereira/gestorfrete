from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.financial.application.commands.create_accounts_payable import (
    CreateAccountsPayableCommand,
    CreateAccountsPayableHandler,
)
from modules.financial.domain.value_objects.payable_origin import PayableOrigin
from modules.financial.infrastructure.persistence.repositories.sqlalchemy_accounts_payable_repository import (
    SqlAlchemyAccountsPayableRepository,
)
from modules.maintenance.application.dtos.ordem_servico_dto import OrdemServicoDTO
from modules.maintenance.domain.entities.ordem_servico import OrdemServico
from modules.maintenance.domain.entities.ordem_servico_status_history_entry import OrdemServicoStatusHistoryEntry
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_ordem_servico_repository import (
    SqlAlchemyOrdemServicoRepository,
)
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_ordem_servico_status_history_repository import (
    SqlAlchemyOrdemServicoStatusHistoryRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class FecharOrdemServicoCommand(Command):
    actor: AuthenticatedActor
    ordem_servico_id: uuid.UUID


class FecharOrdemServicoHandler(CommandHandler[FecharOrdemServicoCommand, OrdemServicoDTO]):
    """`CONCLUIDA→FECHADA` — estado terminal, nunca reaberto. Fecha D387/006-financeiro.md:
    `OrdemServicoFechada` → Conta a Pagar automática, só quando a OS tem `fornecedor_executor_id`
    **e** `centro_custo_id` **e** `plano_contas_id` preenchidos (todos NOT NULL em `contas_pagar`).
    OS 100% mão de obra interna (sem Fornecedor) nunca gera Conta a Pagar automática — não há
    título a pagar a ninguém nesse caso, decisão deliberada, não limitação. Idempotente: verificada
    antes de criar, então a mesma OS nunca gera duas, mesmo em retry. `vehicle_id` vem da própria OS
    (dimensão natural da manutenção); `driver_id` nunca é inferido (nem a OS tem um motorista
    associado por padrão); `trip_id` fica `None` — a OS não tem uma Viagem associada nesta Lote, o
    custo entra só no Centro de Custo, nunca contamina a margem de uma viagem por engano.
    `competencia` deriva do mês de fechamento (única inferência aceitável aqui — é o próprio
    sistema, não um usuário, preenchendo um lançamento automático sem outra fonte de verdade)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: FecharOrdemServicoCommand) -> OrdemServicoDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            os_repo = SqlAlchemyOrdemServicoRepository(uow.session)
            history_repo = SqlAlchemyOrdemServicoStatusHistoryRepository(uow.session)
            payable_repo = SqlAlchemyAccountsPayableRepository(uow.session)

            ordem_servico = await os_repo.get_by_id(command.ordem_servico_id)
            if ordem_servico is None:
                raise NotFoundError("MAINTENANCE_WORK_ORDER_NOT_FOUND", "Ordem de Serviço não encontrada.")

            now = datetime.now(timezone.utc)
            ordem_servico.fechar(now=now, atualizado_por=command.actor.user_id)
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

            already_billed = await payable_repo.exists_for_ordem_servico(ordem_servico.id)

            await uow.commit()

        if not already_billed:
            await self._maybe_create_payable(actor=command.actor, ordem_servico=ordem_servico, now=now)

        return OrdemServicoDTO.from_entity(ordem_servico)

    @staticmethod
    async def _maybe_create_payable(
        *, actor: AuthenticatedActor, ordem_servico: OrdemServico, now: datetime
    ) -> None:
        supplier_id = ordem_servico.fornecedor_executor_id
        cost_center_id = ordem_servico.centro_custo_id
        chart_of_accounts_id = ordem_servico.plano_contas_id
        valor = ordem_servico.custo_realizado
        if supplier_id is None or cost_center_id is None or chart_of_accounts_id is None or valor is None:
            return

        await CreateAccountsPayableHandler().handle(
            CreateAccountsPayableCommand(
                actor=actor, supplier_id=supplier_id, cost_center_id=cost_center_id,
                origem=PayableOrigin.ORDEM_SERVICO, trip_id=None, maintenance_order_id=ordem_servico.id,
                vehicle_id=ordem_servico.veiculo_tracionador_id, driver_id=None, valor=valor,
                data_vencimento=now.date(), competencia=now.date().replace(day=1),
                chart_of_accounts_id=chart_of_accounts_id,
            )
        )
