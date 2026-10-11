from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError
from modules.pricing.application.dtos.price_table_dto import PriceTableItemDTO
from modules.pricing.domain.entities.price_table_item import PriceTableItem
from modules.pricing.domain.value_objects.faixa_distancia_mode import FaixaDistanciaMode
from modules.pricing.domain.value_objects.price_table_status import PriceTableStatus
from modules.pricing.domain.value_objects.price_table_unit import PriceTableUnit
from modules.pricing.infrastructure.persistence.repositories.sqlalchemy_price_table_repository import (
    SqlAlchemyPriceTableRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreatePriceTableItemCommand(Command):
    actor: AuthenticatedActor
    price_table_id: uuid.UUID
    unidade_calculo: PriceTableUnit
    categoria_veiculo_id: uuid.UUID | None
    origem_uf: str | None
    destino_uf: str | None
    faixa_distancia_min_km: Decimal | None
    faixa_distancia_max_km: Decimal | None
    faixa_modo: FaixaDistanciaMode | None
    valor: Decimal
    valor_minimo: Decimal | None
    adicional_fixo: Decimal | None
    desconto_fixo: Decimal | None
    adicional_percentual: Decimal | None
    desconto_percentual: Decimal | None
    base_percentual_descricao: str | None


class CreatePriceTableItemHandler(CommandHandler[CreatePriceTableItemCommand, PriceTableItemDTO]):
    """Item só pode ser criado enquanto a `PriceTable` dona está `RASCUNHO` — assim que `VIGENTE`,
    os itens já aplicados em Viagens precisam continuar íntegros (a Viagem guardou um snapshot
    completo em `TripPriceApplication`, mas o item em si também nunca muda por baixo)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreatePriceTableItemCommand) -> PriceTableItemDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyPriceTableRepository(uow.session)
            table = await repo.get_by_id(command.price_table_id)
            if table is None:
                raise NotFoundError("PRICING_PRICE_TABLE_NOT_FOUND", "Tabela de Frete não encontrada.")
            if table.status != PriceTableStatus.RASCUNHO:
                raise ConflictError(
                    "PRICING_PRICE_TABLE_INVALID_STATUS",
                    f"Tabela está {table.status.value} — itens só podem ser criados enquanto RASCUNHO.",
                )

            item = PriceTableItem.create(
                tabela_preco_id=table.id, unidade_calculo=command.unidade_calculo,
                categoria_veiculo_id=command.categoria_veiculo_id, origem_uf=command.origem_uf,
                destino_uf=command.destino_uf, faixa_distancia_min_km=command.faixa_distancia_min_km,
                faixa_distancia_max_km=command.faixa_distancia_max_km, faixa_modo=command.faixa_modo,
                valor=command.valor, valor_minimo=command.valor_minimo, adicional_fixo=command.adicional_fixo,
                desconto_fixo=command.desconto_fixo, adicional_percentual=command.adicional_percentual,
                desconto_percentual=command.desconto_percentual,
                base_percentual_descricao=command.base_percentual_descricao,
                now=datetime.now(timezone.utc),
            )
            await repo.add_item(item)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="itens_tabela_preco",
                entidade_id=item.id, acao="CRIACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"unidade_calculo": item.unidade_calculo.value, "valor": str(item.valor)},
            )

            await uow.commit()

        return PriceTableItemDTO.from_entity(item)
