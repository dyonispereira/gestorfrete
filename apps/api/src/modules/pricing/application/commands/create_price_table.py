from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from modules.pricing.application.dtos.price_table_dto import PriceTableDTO
from modules.pricing.domain.entities.price_table import PriceTable
from modules.pricing.domain.value_objects.price_table_direction import PriceTableDirection
from modules.pricing.infrastructure.persistence.repositories.sqlalchemy_price_table_repository import (
    SqlAlchemyPriceTableRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor
from shared_kernel.domain.audit_metadata import AuditMetadata


@dataclass(frozen=True)
class CreatePriceTableCommand(Command):
    actor: AuthenticatedActor
    nome: str
    direcao: PriceTableDirection
    vigencia_inicio: date
    vigencia_fim: date | None
    cliente_id: uuid.UUID | None


class CreatePriceTableHandler(CommandHandler[CreatePriceTableCommand, PriceTableDTO]):
    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreatePriceTableCommand) -> PriceTableDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyPriceTableRepository(uow.session)

            now = datetime.now(timezone.utc)
            table = PriceTable.create(
                nome=command.nome, direcao=command.direcao, vigencia_inicio=command.vigencia_inicio,
                vigencia_fim=command.vigencia_fim, cliente_id=command.cliente_id,
                audit=AuditMetadata(
                    created_at=now, created_by=command.actor.user_id, updated_at=now,
                    updated_by=command.actor.user_id,
                ),
            )
            await repo.add(table)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="tabelas_preco",
                entidade_id=table.id, acao="CRIACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"nome": table.nome, "direcao": table.direcao.value},
            )

            await uow.commit()

        return PriceTableDTO.from_entity(table)
