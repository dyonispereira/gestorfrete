from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.pricing.application.dtos.price_table_dto import PriceTableDTO
from modules.pricing.infrastructure.persistence.repositories.sqlalchemy_price_table_repository import (
    SqlAlchemyPriceTableRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdatePriceTableCommand(Command):
    actor: AuthenticatedActor
    price_table_id: uuid.UUID
    nome: str | None
    vigencia_fim: date | None


class UpdatePriceTableHandler(CommandHandler[UpdatePriceTableCommand, PriceTableDTO]):
    async def handle(self, command: UpdatePriceTableCommand) -> PriceTableDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyPriceTableRepository(uow.session)
            table = await repo.get_by_id(command.price_table_id)
            if table is None:
                raise NotFoundError("PRICING_PRICE_TABLE_NOT_FOUND", "Tabela de Frete não encontrada.")

            table.update(
                nome=command.nome, vigencia_fim=command.vigencia_fim, updated_by=command.actor.user_id,
                now=datetime.now(timezone.utc),
            )
            await repo.add(table)
            await uow.commit()

        return PriceTableDTO.from_entity(table)
