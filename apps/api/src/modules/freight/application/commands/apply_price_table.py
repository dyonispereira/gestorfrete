from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError, ValidationError
from modules.freight.application.dtos.trip_dto import TripDTO
from modules.freight.domain.entities.trip_price_application import TripPriceApplication
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_price_application_repository import (
    SqlAlchemyTripPriceApplicationRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from modules.pricing.application.price_calculation_service import calculate
from modules.pricing.domain.value_objects.price_table_direction import PriceTableDirection
from modules.pricing.domain.value_objects.price_table_status import PriceTableStatus
from modules.pricing.infrastructure.persistence.repositories.sqlalchemy_price_table_repository import (
    SqlAlchemyPriceTableRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ApplyPriceTableCommand(Command):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    price_table_item_id: uuid.UUID
    base_percentual_valor: Decimal | None = None


class ApplyPriceTableHandler(CommandHandler[ApplyPriceTableCommand, TripDTO]):
    """Lote 2 (`GESTORFRETE — PROMPT MESTRE`) — aplica um `PriceTableItem` numa Viagem, calcula o
    valor via `pricing.price_calculation_service` (único lugar que faz essa conta) e congela o
    snapshot completo em `TripPriceApplication` (append-only, D109-consistent) + nos dois ponteiros
    de `Trip` (`tabela_preco_aplicada_snapshot_id`/`aplicacao_tabela_preco_atual_id`).

    COMPRA bloqueada nesta fase (`PRICING_PURCHASE_APPLICATION_REQUIRES_CARRIER`) — não existe
    `Transportador`/vínculo contratual ainda (Lote 5, `carriers`); aplicar frete de compra sem um
    credor real seria dado órfão. Lock pessimista na Viagem (mesmo padrão de `DispatchTripHandler`,
    Hotfix P0 Fase 2) contra duas aplicações concorrentes na mesma Viagem."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: ApplyPriceTableCommand) -> TripDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            trip_repo = SqlAlchemyTripRepository(uow.session)
            price_table_repo = SqlAlchemyPriceTableRepository(uow.session)
            application_repo = SqlAlchemyTripPriceApplicationRepository(uow.session)

            trip = await trip_repo.get_by_id_for_update(command.trip_id)
            if trip is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")

            item = await price_table_repo.get_item_by_id(command.price_table_item_id)
            if item is None:
                raise NotFoundError("PRICING_PRICE_TABLE_ITEM_NOT_FOUND", "Item de Tabela de Frete não encontrado.")

            table = await price_table_repo.get_by_id(item.tabela_preco_id)
            if table is None:  # pragma: no cover - integridade referencial garante isso na prática
                raise NotFoundError("PRICING_PRICE_TABLE_NOT_FOUND", "Tabela de Frete não encontrada.")
            if table.status != PriceTableStatus.VIGENTE:
                raise ValidationError(
                    "PRICING_PRICE_TABLE_NOT_VIGENTE", f"Tabela de Frete está {table.status.value}, não VIGENTE."
                )
            if table.direcao == PriceTableDirection.COMPRA:
                raise ConflictError(
                    "PRICING_PURCHASE_APPLICATION_REQUIRES_CARRIER",
                    "Aplicação de Tabela de Frete de COMPRA exige Transportador/vínculo contratual "
                    "válido — ainda não implementado (Lote 5).",
                )

            result = calculate(
                item, distancia_prevista_km=trip.distancia_prevista_km, toneladas_carga=trip.toneladas_carga,
                peso_carga_kg=trip.peso_carga_kg, base_percentual_valor=command.base_percentual_valor,
            )

            now = datetime.now(timezone.utc)
            application = TripPriceApplication.create(
                viagem_id=trip.id, tabela_preco_id=table.id, item_tabela_preco_id=item.id,
                tabela_preco_versao=table.versao, direcao=table.direcao.value,
                unidade_calculo=item.unidade_calculo.value, quantidade_utilizada=result.quantidade_utilizada,
                base_percentual_valor=command.base_percentual_valor, tarifa_aplicada=item.valor,
                valor_minimo_aplicado=item.valor_minimo, adicional_fixo_aplicado=item.adicional_fixo,
                desconto_fixo_aplicado=item.desconto_fixo, adicional_percentual_aplicado=item.adicional_percentual,
                desconto_percentual_aplicado=item.desconto_percentual,
                valor_calculado_bruto=result.valor_calculado_bruto, valor_final=result.valor_final,
                aplicado_por=command.actor.user_id, now=now,
            )
            await application_repo.create(application)

            trip.apply_price_table(
                tabela_preco_id=table.id, aplicacao_id=application.id, receita_prevista_snapshot=result.valor_final
            )
            await trip_repo.add(trip)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="viagens", entidade_id=trip.id,
                acao="ALTERACAO", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={
                    "tabela_preco_id": str(table.id), "receita_prevista_snapshot": str(result.valor_final),
                },
            )

            await uow.commit()

        return TripDTO.from_entity(trip)
