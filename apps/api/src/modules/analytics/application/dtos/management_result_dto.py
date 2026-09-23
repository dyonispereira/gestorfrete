from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from modules.analytics.infrastructure.persistence.repositories.management_result_read_repository import (
    TripAggregate,
)

_ZERO = Decimal("0")
_CENTS = Decimal("0.01")


@dataclass(frozen=True)
class ResultTotals:
    """KPIs fundamentais pedidos pelo usuário, iguais em forma nas 4 dimensões (só o agrupamento
    de origem muda). `predicted_margin`/`realized_margin_pct`/`*_per_km` ficam `None` quando não há
    base para calcular (sem receita realizada, sem KM) — nunca um 0 fabricado no lugar de um dado
    inexistente."""

    trips: int
    predicted_revenue: Decimal
    realized_revenue: Decimal
    predicted_cost: Decimal
    realized_cost: Decimal
    realized_margin: Decimal
    predicted_margin: Decimal
    realized_margin_pct: Decimal | None
    km: Decimal | None
    revenue_per_km: Decimal | None
    cost_per_km: Decimal | None
    margin_per_km: Decimal | None


def _round(value: Decimal) -> Decimal:
    return value.quantize(_CENTS, rounding=ROUND_HALF_UP)


def build_totals(
    agg: TripAggregate, *, extra_realized_cost: Decimal = _ZERO, extra_predicted_cost: Decimal = _ZERO
) -> ResultTotals:
    """Função pura, reusada por Visão Geral/Viagem/Veículo/Cliente/Motorista — `extra_realized_cost`
    carrega Manutenção+Outros Custos (Veículo) ou lançamentos vinculados (Motorista); nas demais
    dimensões fica em zero. Nunca soma o mesmo real duas vezes: cada bucket de custo só entra na
    conta de uma única dimensão por vez (docs/domain/012-resultado-gerencial.md)."""

    realized_cost = agg.realized_cost + extra_realized_cost
    predicted_cost = agg.predicted_cost + extra_predicted_cost
    realized_margin = agg.realized_revenue - realized_cost
    predicted_margin = agg.predicted_revenue - predicted_cost
    realized_margin_pct = (
        _round((realized_margin / agg.realized_revenue) * Decimal("100")) if agg.realized_revenue != _ZERO else None
    )
    km = agg.km if agg.km is not None and agg.km > _ZERO else None
    return ResultTotals(
        trips=agg.trip_count,
        predicted_revenue=_round(agg.predicted_revenue),
        realized_revenue=_round(agg.realized_revenue),
        predicted_cost=_round(predicted_cost),
        realized_cost=_round(realized_cost),
        realized_margin=_round(realized_margin),
        predicted_margin=_round(predicted_margin),
        realized_margin_pct=realized_margin_pct,
        km=km,
        revenue_per_km=_round(agg.realized_revenue / km) if km is not None else None,
        cost_per_km=_round(realized_cost / km) if km is not None else None,
        margin_per_km=_round(realized_margin / km) if km is not None else None,
    )


@dataclass(frozen=True)
class TripResultDTO:
    trip_id: uuid.UUID
    codigo: str
    data_programada: date | None
    client_id: uuid.UUID
    client_name: str | None
    driver_id: uuid.UUID | None
    driver_name: str | None
    vehicle_id: uuid.UUID | None
    vehicle_plate: str | None
    totals: ResultTotals


@dataclass(frozen=True)
class VehicleResultDTO:
    """Distingue explicitamente Resultado Operacional de Viagens (só o que a Viagem gerou) de
    Resultado Total do Veículo (inclui Manutenção + Outros Custos do ativo) — pedido central do
    usuário: um caminhão pode parecer ótimo nas viagens e consumir tudo fora delas."""

    vehicle_id: uuid.UUID
    plate: str
    model: str
    trip_cost_realized: Decimal
    maintenance_cost_predicted: Decimal
    maintenance_cost_realized: Decimal
    other_costs_realized: Decimal
    operational_result: Decimal
    operational_margin_pct: Decimal | None
    # V1 Operational Hardening, Parte 3 — "Custo operacional/km" (só Viagens) vs. `totals.cost_per_km`
    # ("Custo total/km", inclui Manutenção+Outros Custos) — mesma distinção Operacional×Total de cima,
    # levada ao KM. `None` sob a mesma regra de `totals.km` (nunca uma fração de KM indisponível).
    operational_cost_per_km: Decimal | None
    operational_result_per_km: Decimal | None
    totals: ResultTotals


@dataclass(frozen=True)
class ClientResultDTO:
    client_id: uuid.UUID
    name: str
    trade_name: str | None
    totals: ResultTotals


@dataclass(frozen=True)
class DriverResultDTO:
    driver_id: uuid.UUID
    name: str
    trip_cost_realized: Decimal
    linked_cost_realized: Decimal
    totals: ResultTotals


@dataclass(frozen=True)
class OverviewResultDTO:
    """`other_costs_realized` é uma soma única, não-agrupada (nunca a soma de "Outros Custos por
    Veículo" + "custo vinculado por Motorista" — essas duas visões podem compartilhar a mesma Conta
    a Pagar quando ela está tagueada em ambas as dimensões ao mesmo tempo; somar as duas contaria o
    mesmo real duas vezes)."""

    totals: ResultTotals
    maintenance_cost_realized: Decimal
    other_costs_realized: Decimal


@dataclass(frozen=True)
class VehicleCostOriginDTO:
    """Item de drill-down "Veículo → custos → OS/CP de origem"."""

    accounts_payable_id: uuid.UUID
    origin: str
    maintenance_order_id: uuid.UUID | None
    value: Decimal
    competencia: date
    status: str


@dataclass(frozen=True)
class VehicleResultDetailDTO:
    result: VehicleResultDTO
    trips: list[TripResultDTO] = field(default_factory=list)
    cost_origins: list[VehicleCostOriginDTO] = field(default_factory=list)


@dataclass(frozen=True)
class ClientInvoiceSummaryDTO:
    invoice_id: uuid.UUID
    invoice_number: str
    issue_date: date
    status: str
    total_value: Decimal
    trip_count: int


@dataclass(frozen=True)
class ClientResultDetailDTO:
    result: ClientResultDTO
    trips: list[TripResultDTO] = field(default_factory=list)
    invoices: list[ClientInvoiceSummaryDTO] = field(default_factory=list)


@dataclass(frozen=True)
class DriverLinkedCostDTO:
    accounts_payable_id: uuid.UUID
    origin: str
    value: Decimal
    competencia: date
    status: str


@dataclass(frozen=True)
class DriverResultDetailDTO:
    result: DriverResultDTO
    trips: list[TripResultDTO] = field(default_factory=list)
    linked_costs: list[DriverLinkedCostDTO] = field(default_factory=list)
