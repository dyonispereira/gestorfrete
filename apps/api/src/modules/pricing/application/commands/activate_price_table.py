from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError, ValidationError
from modules.pricing.application.dtos.price_table_dto import PriceTableDTO
from modules.pricing.infrastructure.persistence.repositories.sqlalchemy_price_table_repository import (
    SqlAlchemyPriceTableRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ActivatePriceTableCommand(Command):
    actor: AuthenticatedActor
    price_table_id: uuid.UUID


class ActivatePriceTableHandler(CommandHandler[ActivatePriceTableCommand, PriceTableDTO]):
    """RASCUNHO→VIGENTE — exige ao menos 1 item (tabela vigente sem item nenhum nunca seria
    aplicável, erro de operação quase certo)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: ActivatePriceTableCommand) -> PriceTableDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyPriceTableRepository(uow.session)
            table = await repo.get_by_id(command.price_table_id)
            if table is None:
                raise NotFoundError("PRICING_PRICE_TABLE_NOT_FOUND", "Tabela de Frete não encontrada.")

            items = await repo.get_items(table.id)
            if not items:
                raise ValidationError(
                    "PRICING_PRICE_TABLE_NO_ITEMS", "Tabela de Frete precisa de ao menos 1 item para ser ativada."
                )

            table.activate(updated_by=command.actor.user_id, now=datetime.now(timezone.utc))
            await repo.add(table)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="tabelas_preco",
                entidade_id=table.id, acao="TRANSICAO_STATUS", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id), dados_depois={"status": table.status.value},
            )

            await uow.commit()

        return PriceTableDTO.from_entity(table)
