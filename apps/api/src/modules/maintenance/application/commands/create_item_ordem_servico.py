from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError
from modules.maintenance.application.dtos.item_ordem_servico_dto import ItemOrdemServicoDTO
from modules.maintenance.domain.entities.item_ordem_servico import ItemOrdemServico
from modules.maintenance.domain.value_objects.item_ordem_servico_categoria_custo import (
    ItemOrdemServicoCategoriaCusto,
)
from modules.maintenance.domain.value_objects.ordem_servico_status import OrdemServicoStatus
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_item_ordem_servico_repository import (
    SqlAlchemyItemOrdemServicoRepository,
)
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_ordem_servico_repository import (
    SqlAlchemyOrdemServicoRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor

_STATUS_QUE_ACEITAM_ITEM = frozenset({
    OrdemServicoStatus.ABERTA, OrdemServicoStatus.EM_DIAGNOSTICO, OrdemServicoStatus.AGUARDANDO_APROVACAO,
    OrdemServicoStatus.EM_EXECUCAO,
})


@dataclass(frozen=True)
class CreateItemOrdemServicoCommand(Command):
    actor: AuthenticatedActor
    ordem_servico_id: uuid.UUID
    categoria_custo: str
    descricao: str
    quantidade: Decimal
    valor_unitario: Decimal
    peca_estoque_id: uuid.UUID | None = None


class CreateItemOrdemServicoHandler(CommandHandler[CreateItemOrdemServicoCommand, ItemOrdemServicoDTO]):
    """Recalcula `custo_previsto` da OS a cada item adicionado (D086) — nunca um campo digitado
    diretamente. Bloqueado depois de `CONCLUIDA`/`FECHADA`/`CANCELADA` — itens não fazem sentido
    numa OS já encerrada."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateItemOrdemServicoCommand) -> ItemOrdemServicoDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            os_repo = SqlAlchemyOrdemServicoRepository(uow.session)
            item_repo = SqlAlchemyItemOrdemServicoRepository(uow.session)

            ordem_servico = await os_repo.get_by_id(command.ordem_servico_id)
            if ordem_servico is None:
                raise NotFoundError("MAINTENANCE_WORK_ORDER_NOT_FOUND", "Ordem de Serviço não encontrada.")
            if ordem_servico.status not in _STATUS_QUE_ACEITAM_ITEM:
                raise ConflictError(
                    "MAINTENANCE_WORK_ORDER_ITEM_NOT_ALLOWED",
                    f"Ordem de Serviço em {ordem_servico.status.value} não aceita novos itens.",
                )

            item = ItemOrdemServico.create(
                ordem_servico_id=command.ordem_servico_id, categoria_custo=ItemOrdemServicoCategoriaCusto(command.categoria_custo),
                descricao=command.descricao, peca_estoque_id=command.peca_estoque_id, quantidade=command.quantidade,
                valor_unitario=command.valor_unitario,
            )
            await item_repo.add(item)

            itens = await item_repo.list_for_ordem_servico(command.ordem_servico_id)
            total = sum((i.valor_total for i in itens), Decimal("0.00"))
            now = datetime.now(timezone.utc)
            ordem_servico.recompute_custo_previsto(value=total)
            ordem_servico.atualizado_em = now
            ordem_servico.atualizado_por = command.actor.user_id
            await os_repo.add(ordem_servico)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="itens_ordem_servico",
                entidade_id=item.id, acao="CRIACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"ordem_servico_id": str(command.ordem_servico_id), "valor_total": str(item.valor_total)},
            )
            await uow.commit()

        return ItemOrdemServicoDTO.from_entity(item)
