from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError
from modules.pricing.domain.value_objects.price_table_status import PriceTableStatus
from modules.pricing.infrastructure.persistence.repositories.sqlalchemy_price_table_repository import (
    SqlAlchemyPriceTableRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class DeletePriceTableItemCommand(Command):
    actor: AuthenticatedActor
    price_table_id: uuid.UUID
    item_id: uuid.UUID


class DeletePriceTableItemHandler(CommandHandler[DeletePriceTableItemCommand, None]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: DeletePriceTableItemCommand) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyPriceTableRepository(uow.session)
            table = await repo.get_by_id(command.price_table_id)
            if table is None:
                raise NotFoundError("PRICING_PRICE_TABLE_NOT_FOUND", "Tabela de Frete não encontrada.")
            if table.status != PriceTableStatus.RASCUNHO:
                raise ConflictError(
                    "PRICING_PRICE_TABLE_INVALID_STATUS",
                    f"Tabela está {table.status.value} — itens só podem ser removidos enquanto RASCUNHO.",
                )

            item = await repo.get_item_by_id(command.item_id)
            if item is None or item.tabela_preco_id != command.price_table_id:
                raise NotFoundError("PRICING_PRICE_TABLE_ITEM_NOT_FOUND", "Item não encontrado nesta tabela.")

            await repo.delete_item(command.item_id)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="itens_tabela_preco",
                entidade_id=item.id, acao="EXCLUSAO_LOGICA", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )

            await uow.commit()
