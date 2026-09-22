from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from modules.crm.infrastructure.persistence.models.client_model import ClientModel
from modules.drivers.infrastructure.persistence.models.driver_model import DriverModel
from modules.financial.domain.value_objects.payable_origin import PayableOrigin
from modules.financial.domain.value_objects.payable_status import PayableStatus
from modules.financial.infrastructure.persistence.models.accounts_payable_model import AccountsPayableModel
from modules.financial.infrastructure.persistence.models.invoice_model import InvoiceModel, InvoiceTripModel
from modules.fleet.infrastructure.persistence.models.vehicle_model import VehicleModel
from modules.freight.domain.value_objects.trip_operational_status import TripOperationalStatus
from modules.freight.infrastructure.persistence.models.trip_model import TripModel
from modules.maintenance.domain.value_objects.ordem_servico_status import OrdemServicoStatus
from modules.maintenance.infrastructure.persistence.models.ordem_servico_model import OrdemServicoModel

_ZERO = Decimal("0")


@dataclass(frozen=True)
class TripAggregate:
    """Soma pura das colunas já-realizadas/previstas de `viagens` (D008/D090 — Resultado Gerencial
    nunca recalcula o que `freight`/`financial` já são donos de calcular, só agrega). Base comum de
    Visão Geral/Viagem/Veículo/Cliente/Motorista — cada dimensão só muda o `GROUP BY`, nunca a
    fórmula. `km` fica `None` quando nenhuma Viagem do grupo tem `km_rodado` preenchido (gap
    registrado em `docs/domain/012-resultado-gerencial.md` — nunca aproximado)."""

    trip_count: int
    predicted_revenue: Decimal
    realized_revenue: Decimal
    predicted_cost: Decimal
    realized_cost: Decimal
    km: Decimal | None


def _trip_base_filters(
    tenant_id: uuid.UUID, date_from: date | None, date_to: date | None
) -> list[ColumnElement[Any]]:
    filters: list[ColumnElement[Any]] = [
        TripModel.tenant_id == tenant_id,
        TripModel.excluido_em.is_(None),
        TripModel.status_operacional != TripOperationalStatus.CANCELADA.value,
    ]
    if date_from is not None:
        filters.append(TripModel.data_programada >= date_from)
    if date_to is not None:
        filters.append(TripModel.data_programada <= date_to)
    return filters


def _row_to_trip_aggregate(row: tuple[Any, ...]) -> TripAggregate:
    return TripAggregate(
        trip_count=row[0], predicted_revenue=row[1], realized_revenue=row[2],
        predicted_cost=row[3], realized_cost=row[4], km=row[5],
    )


class ManagementResultReadRepository:
    """Lote 4 — Resultado Gerencial. Só leitura, cross-module (D090/D149 — `analytics` lê
    `freight`/`financial`/`maintenance`/`fleet`/`drivers`/`crm` diretamente, nunca o inverso — já
    sancionado pelo import-linter). Nenhuma entidade nova, nenhuma cópia de valor: toda soma é
    calculada aqui, na hora, a partir das colunas já autoritativas de cada módulo dono."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Base Viagem — Receita/Custo Previsto/Realizado, previstos por `freight`.
    # ------------------------------------------------------------------

    async def trip_overview(self, *, tenant_id: uuid.UUID, date_from: date | None, date_to: date | None) -> TripAggregate:
        stmt = select(
            func.count(TripModel.id),
            func.coalesce(func.sum(TripModel.receita_prevista_snapshot), _ZERO),
            func.coalesce(func.sum(TripModel.receita_realizada), _ZERO),
            func.coalesce(func.sum(TripModel.custo_previsto), _ZERO),
            func.coalesce(func.sum(TripModel.custo_realizado), _ZERO),
            func.sum(TripModel.km_rodado),
        ).where(*_trip_base_filters(tenant_id, date_from, date_to))
        row = (await self._session.execute(stmt)).one()
        return _row_to_trip_aggregate(tuple(row))

    async def trip_aggregates_by_client(
        self, *, tenant_id: uuid.UUID, date_from: date | None, date_to: date | None
    ) -> dict[uuid.UUID, TripAggregate]:
        return await self._trip_aggregates_grouped(TripModel.cliente_id, tenant_id, date_from, date_to)

    async def trip_aggregates_by_vehicle(
        self, *, tenant_id: uuid.UUID, date_from: date | None, date_to: date | None
    ) -> dict[uuid.UUID, TripAggregate]:
        return await self._trip_aggregates_grouped(TripModel.veiculo_tracionador_id, tenant_id, date_from, date_to)

    async def trip_aggregates_by_driver(
        self, *, tenant_id: uuid.UUID, date_from: date | None, date_to: date | None
    ) -> dict[uuid.UUID, TripAggregate]:
        return await self._trip_aggregates_grouped(TripModel.motorista_id, tenant_id, date_from, date_to)

    async def _trip_aggregates_grouped(
        self,
        group_by_column: InstrumentedAttribute[Any],
        tenant_id: uuid.UUID,
        date_from: date | None,
        date_to: date | None,
    ) -> dict[uuid.UUID, TripAggregate]:
        stmt = (
            select(
                group_by_column,
                func.count(TripModel.id),
                func.coalesce(func.sum(TripModel.receita_prevista_snapshot), _ZERO),
                func.coalesce(func.sum(TripModel.receita_realizada), _ZERO),
                func.coalesce(func.sum(TripModel.custo_previsto), _ZERO),
                func.coalesce(func.sum(TripModel.custo_realizado), _ZERO),
                func.sum(TripModel.km_rodado),
            )
            .where(*_trip_base_filters(tenant_id, date_from, date_to), group_by_column.is_not(None))
            .group_by(group_by_column)
        )
        rows = (await self._session.execute(stmt)).all()
        return {row[0]: _row_to_trip_aggregate(tuple(row[1:])) for row in rows}

    async def list_trips(
        self,
        *,
        tenant_id: uuid.UUID,
        date_from: date | None,
        date_to: date | None,
        client_id: uuid.UUID | None = None,
        vehicle_id: uuid.UUID | None = None,
        driver_id: uuid.UUID | None = None,
        page: int,
        limit: int,
    ) -> tuple[list[TripModel], int]:
        filters = _trip_base_filters(tenant_id, date_from, date_to)
        if client_id is not None:
            filters.append(TripModel.cliente_id == client_id)
        if vehicle_id is not None:
            filters.append(TripModel.veiculo_tracionador_id == vehicle_id)
        if driver_id is not None:
            filters.append(TripModel.motorista_id == driver_id)
        total = (await self._session.execute(select(func.count()).select_from(TripModel).where(*filters))).scalar_one()
        stmt = (
            select(TripModel)
            .where(*filters)
            .order_by(TripModel.data_programada.desc().nullslast(), TripModel.criado_em.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return list(rows), total

    # ------------------------------------------------------------------
    # Custos fora de Viagem — Manutenção (por Ordem de Serviço) e Outros Custos, ambos por Veículo.
    # ------------------------------------------------------------------

    async def maintenance_realized_by_vehicle(
        self, *, tenant_id: uuid.UUID, date_from: date | None, date_to: date | None
    ) -> dict[uuid.UUID, Decimal]:
        filters = [
            AccountsPayableModel.tenant_id == tenant_id,
            AccountsPayableModel.excluido_em.is_(None),
            AccountsPayableModel.origem == PayableOrigin.ORDEM_SERVICO.value,
            AccountsPayableModel.status != PayableStatus.REJEITADA.value,
            OrdemServicoModel.status != OrdemServicoStatus.CANCELADA.value,
        ]
        if date_from is not None:
            filters.append(AccountsPayableModel.competencia >= date_from)
        if date_to is not None:
            filters.append(AccountsPayableModel.competencia <= date_to)
        stmt = (
            select(OrdemServicoModel.veiculo_tracionador_id, func.coalesce(func.sum(AccountsPayableModel.valor), _ZERO))
            .select_from(AccountsPayableModel)
            .join(OrdemServicoModel, AccountsPayableModel.ordem_servico_id == OrdemServicoModel.id)
            .where(*filters)
            .group_by(OrdemServicoModel.veiculo_tracionador_id)
        )
        rows = (await self._session.execute(stmt)).all()
        return {row[0]: row[1] for row in rows}

    async def maintenance_predicted_by_vehicle(
        self, *, tenant_id: uuid.UUID, date_from: date | None, date_to: date | None
    ) -> dict[uuid.UUID, Decimal]:
        filters: list[ColumnElement[Any]] = [
            OrdemServicoModel.tenant_id == tenant_id,
            OrdemServicoModel.excluido_em.is_(None),
            OrdemServicoModel.status != OrdemServicoStatus.CANCELADA.value,
        ]
        if date_from is not None:
            filters.append(func.date(OrdemServicoModel.criado_em) >= date_from)
        if date_to is not None:
            filters.append(func.date(OrdemServicoModel.criado_em) <= date_to)
        stmt = (
            select(
                OrdemServicoModel.veiculo_tracionador_id,
                func.coalesce(func.sum(OrdemServicoModel.custo_previsto), _ZERO),
            )
            .where(*filters)
            .group_by(OrdemServicoModel.veiculo_tracionador_id)
        )
        rows = (await self._session.execute(stmt)).all()
        return {row[0]: row[1] for row in rows}

    async def other_vehicle_costs_realized(
        self, *, tenant_id: uuid.UUID, date_from: date | None, date_to: date | None
    ) -> dict[uuid.UUID, Decimal]:
        filters: list[ColumnElement[Any]] = [
            AccountsPayableModel.tenant_id == tenant_id,
            AccountsPayableModel.excluido_em.is_(None),
            AccountsPayableModel.veiculo_tracionador_id.is_not(None),
            AccountsPayableModel.origem.notin_([PayableOrigin.VIAGEM.value, PayableOrigin.ORDEM_SERVICO.value]),
            AccountsPayableModel.status != PayableStatus.REJEITADA.value,
        ]
        if date_from is not None:
            filters.append(AccountsPayableModel.competencia >= date_from)
        if date_to is not None:
            filters.append(AccountsPayableModel.competencia <= date_to)
        stmt = (
            select(AccountsPayableModel.veiculo_tracionador_id, func.coalesce(func.sum(AccountsPayableModel.valor), _ZERO))
            .where(*filters)
            .group_by(AccountsPayableModel.veiculo_tracionador_id)
        )
        rows = (await self._session.execute(stmt)).all()
        return {row[0]: row[1] for row in rows}

    async def other_costs_realized_total(
        self, *, tenant_id: uuid.UUID, date_from: date | None, date_to: date | None
    ) -> Decimal:
        """Soma única, não-agrupada, de todo custo fora de Viagem/Manutenção (Lote 4 — Visão Geral).
        Deliberadamente SEM filtro de `veiculo_tracionador_id`/`motorista_id`: uma mesma Conta a
        Pagar pode estar tagueada em ambos ao mesmo tempo, e `other_vehicle_costs_realized`/
        `driver_linked_costs_realized` (agrupados, usados nas dimensões Veículo/Motorista) podem
        legitimamente compartilhar a mesma linha entre si — somar os dois agrupados na Visão Geral
        contaria esse real duas vezes. Esta soma conta cada Conta a Pagar exatamente uma vez."""
        filters: list[ColumnElement[Any]] = [
            AccountsPayableModel.tenant_id == tenant_id,
            AccountsPayableModel.excluido_em.is_(None),
            AccountsPayableModel.origem.notin_([PayableOrigin.VIAGEM.value, PayableOrigin.ORDEM_SERVICO.value]),
            AccountsPayableModel.status != PayableStatus.REJEITADA.value,
        ]
        if date_from is not None:
            filters.append(AccountsPayableModel.competencia >= date_from)
        if date_to is not None:
            filters.append(AccountsPayableModel.competencia <= date_to)
        stmt = select(func.coalesce(func.sum(AccountsPayableModel.valor), _ZERO)).where(*filters)
        return (await self._session.execute(stmt)).scalar_one()

    async def list_vehicle_cost_payables(
        self,
        *,
        tenant_id: uuid.UUID,
        vehicle_id: uuid.UUID,
        date_from: date | None,
        date_to: date | None,
    ) -> list[AccountsPayableModel]:
        """Drill-down "Veículo → custos → OS/CP de origem" — Manutenção (via OS) + Outros Custos
        (tagueados direto no Veículo), a mesma dupla filtrada em `maintenance_realized_by_vehicle`/
        `other_vehicle_costs_realized`, mas devolvendo as linhas em vez da soma."""
        filters: list[ColumnElement[Any]] = [
            AccountsPayableModel.tenant_id == tenant_id,
            AccountsPayableModel.excluido_em.is_(None),
            AccountsPayableModel.status != PayableStatus.REJEITADA.value,
        ]
        if date_from is not None:
            filters.append(AccountsPayableModel.competencia >= date_from)
        if date_to is not None:
            filters.append(AccountsPayableModel.competencia <= date_to)
        maintenance_stmt = (
            select(AccountsPayableModel)
            .join(OrdemServicoModel, AccountsPayableModel.ordem_servico_id == OrdemServicoModel.id)
            .where(
                *filters,
                AccountsPayableModel.origem == PayableOrigin.ORDEM_SERVICO.value,
                OrdemServicoModel.veiculo_tracionador_id == vehicle_id,
                OrdemServicoModel.status != OrdemServicoStatus.CANCELADA.value,
            )
        )
        other_stmt = select(AccountsPayableModel).where(
            *filters,
            AccountsPayableModel.origem.notin_([PayableOrigin.VIAGEM.value, PayableOrigin.ORDEM_SERVICO.value]),
            AccountsPayableModel.veiculo_tracionador_id == vehicle_id,
        )
        maintenance_rows = (await self._session.execute(maintenance_stmt)).scalars().all()
        other_rows = (await self._session.execute(other_stmt)).scalars().all()
        return [*maintenance_rows, *other_rows]

    # ------------------------------------------------------------------
    # Custos vinculados explicitamente ao Motorista (fora de Viagem — nunca herdados do Veículo).
    # ------------------------------------------------------------------

    async def driver_linked_costs_realized(
        self, *, tenant_id: uuid.UUID, date_from: date | None, date_to: date | None
    ) -> dict[uuid.UUID, Decimal]:
        filters = self._driver_linked_cost_filters(tenant_id, date_from, date_to)
        stmt = (
            select(AccountsPayableModel.motorista_id, func.coalesce(func.sum(AccountsPayableModel.valor), _ZERO))
            .where(*filters)
            .group_by(AccountsPayableModel.motorista_id)
        )
        rows = (await self._session.execute(stmt)).all()
        return {row[0]: row[1] for row in rows}

    async def list_driver_linked_payables(
        self, *, tenant_id: uuid.UUID, driver_id: uuid.UUID, date_from: date | None, date_to: date | None
    ) -> list[AccountsPayableModel]:
        filters = self._driver_linked_cost_filters(tenant_id, date_from, date_to)
        stmt = select(AccountsPayableModel).where(*filters, AccountsPayableModel.motorista_id == driver_id)
        return list((await self._session.execute(stmt)).scalars().all())

    @staticmethod
    def _driver_linked_cost_filters(
        tenant_id: uuid.UUID, date_from: date | None, date_to: date | None
    ) -> list[ColumnElement[Any]]:
        filters: list[ColumnElement[Any]] = [
            AccountsPayableModel.tenant_id == tenant_id,
            AccountsPayableModel.excluido_em.is_(None),
            AccountsPayableModel.motorista_id.is_not(None),
            AccountsPayableModel.origem != PayableOrigin.VIAGEM.value,
            AccountsPayableModel.status != PayableStatus.REJEITADA.value,
        ]
        if date_from is not None:
            filters.append(AccountsPayableModel.competencia >= date_from)
        if date_to is not None:
            filters.append(AccountsPayableModel.competencia <= date_to)
        return filters

    # ------------------------------------------------------------------
    # Drill-down Cliente → Faturas.
    # ------------------------------------------------------------------

    async def list_invoices_for_client(
        self, *, tenant_id: uuid.UUID, client_id: uuid.UUID, date_from: date | None, date_to: date | None
    ) -> list[InvoiceModel]:
        filters: list[ColumnElement[Any]] = [
            InvoiceModel.tenant_id == tenant_id,
            InvoiceModel.excluido_em.is_(None),
            InvoiceModel.cliente_id == client_id,
        ]
        if date_from is not None:
            filters.append(InvoiceModel.data_emissao >= date_from)
        if date_to is not None:
            filters.append(InvoiceModel.data_emissao <= date_to)
        stmt = select(InvoiceModel).where(*filters).order_by(InvoiceModel.data_emissao.desc())
        return list((await self._session.execute(stmt)).scalars().all())

    async def count_invoice_trips_for_invoices(self, invoice_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
        if not invoice_ids:
            return {}
        stmt = (
            select(InvoiceTripModel.fatura_id, func.count(InvoiceTripModel.id))
            .where(InvoiceTripModel.fatura_id.in_(invoice_ids))
            .group_by(InvoiceTripModel.fatura_id)
        )
        rows = (await self._session.execute(stmt)).all()
        return {row[0]: row[1] for row in rows}

    # ------------------------------------------------------------------
    # Identidade das dimensões (placa/nome/razão social) — batch, evita N+1 (mesmo padrão de
    # `find_actors_batch`/`list_for_invoices_batch`, Lote Financeiro Parte 2.1/Parte 3).
    # ------------------------------------------------------------------

    async def fetch_vehicle_identities(
        self, *, tenant_id: uuid.UUID, vehicle_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, tuple[str, str]]:
        if not vehicle_ids:
            return {}
        stmt = select(VehicleModel.id, VehicleModel.placa, VehicleModel.modelo).where(
            VehicleModel.tenant_id == tenant_id, VehicleModel.id.in_(vehicle_ids)
        )
        rows = (await self._session.execute(stmt)).all()
        return {row[0]: (row[1], row[2]) for row in rows}

    async def fetch_driver_identities(
        self, *, tenant_id: uuid.UUID, driver_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, str]:
        if not driver_ids:
            return {}
        stmt = select(DriverModel.id, DriverModel.nome).where(
            DriverModel.tenant_id == tenant_id, DriverModel.id.in_(driver_ids)
        )
        rows = (await self._session.execute(stmt)).all()
        return {row[0]: row[1] for row in rows}

    async def fetch_client_identities(
        self, *, tenant_id: uuid.UUID, client_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, tuple[str, str | None]]:
        if not client_ids:
            return {}
        stmt = select(ClientModel.id, ClientModel.razao_social, ClientModel.nome_fantasia).where(
            ClientModel.tenant_id == tenant_id, ClientModel.id.in_(client_ids)
        )
        rows = (await self._session.execute(stmt)).all()
        return {row[0]: (row[1], row[2]) for row in rows}
