from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from modules.analytics.application.dtos.management_result_dto import (
    ClientInvoiceSummaryDTO,
    ClientResultDetailDTO,
    ClientResultDTO,
    DriverLinkedCostDTO,
    DriverResultDetailDTO,
    DriverResultDTO,
    OverviewResultDTO,
    ResultTotals,
    TripResultDTO,
    VehicleCostOriginDTO,
    VehicleResultDetailDTO,
    VehicleResultDTO,
)


class ResultTotalsResponse(BaseModel):
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

    @staticmethod
    def from_dto(t: ResultTotals) -> "ResultTotalsResponse":
        return ResultTotalsResponse(
            trips=t.trips, predicted_revenue=t.predicted_revenue, realized_revenue=t.realized_revenue,
            predicted_cost=t.predicted_cost, realized_cost=t.realized_cost, realized_margin=t.realized_margin,
            predicted_margin=t.predicted_margin, realized_margin_pct=t.realized_margin_pct, km=t.km,
            revenue_per_km=t.revenue_per_km, cost_per_km=t.cost_per_km, margin_per_km=t.margin_per_km,
        )


class OverviewResultResponse(BaseModel):
    totals: ResultTotalsResponse
    maintenance_cost_realized: Decimal
    other_costs_realized: Decimal

    @staticmethod
    def from_dto(dto: OverviewResultDTO) -> "OverviewResultResponse":
        return OverviewResultResponse(
            totals=ResultTotalsResponse.from_dto(dto.totals),
            maintenance_cost_realized=dto.maintenance_cost_realized,
            other_costs_realized=dto.other_costs_realized,
        )


class TripResultResponse(BaseModel):
    trip_id: uuid.UUID
    codigo: str
    scheduled_date: date | None
    client_id: uuid.UUID
    client_name: str | None
    driver_id: uuid.UUID | None
    driver_name: str | None
    vehicle_id: uuid.UUID | None
    vehicle_plate: str | None
    totals: ResultTotalsResponse

    @staticmethod
    def from_dto(dto: TripResultDTO) -> "TripResultResponse":
        return TripResultResponse(
            trip_id=dto.trip_id, codigo=dto.codigo, scheduled_date=dto.data_programada,
            client_id=dto.client_id, client_name=dto.client_name, driver_id=dto.driver_id,
            driver_name=dto.driver_name, vehicle_id=dto.vehicle_id, vehicle_plate=dto.vehicle_plate,
            totals=ResultTotalsResponse.from_dto(dto.totals),
        )


class VehicleResultResponse(BaseModel):
    vehicle_id: uuid.UUID
    plate: str
    model: str
    trip_cost_realized: Decimal
    maintenance_cost_predicted: Decimal
    maintenance_cost_realized: Decimal
    other_costs_realized: Decimal
    operational_result: Decimal
    operational_margin_pct: Decimal | None
    totals: ResultTotalsResponse

    @staticmethod
    def from_dto(dto: VehicleResultDTO) -> "VehicleResultResponse":
        return VehicleResultResponse(
            vehicle_id=dto.vehicle_id, plate=dto.plate, model=dto.model,
            trip_cost_realized=dto.trip_cost_realized,
            maintenance_cost_predicted=dto.maintenance_cost_predicted,
            maintenance_cost_realized=dto.maintenance_cost_realized,
            other_costs_realized=dto.other_costs_realized, operational_result=dto.operational_result,
            operational_margin_pct=dto.operational_margin_pct, totals=ResultTotalsResponse.from_dto(dto.totals),
        )


class ClientResultResponse(BaseModel):
    client_id: uuid.UUID
    name: str
    trade_name: str | None
    totals: ResultTotalsResponse

    @staticmethod
    def from_dto(dto: ClientResultDTO) -> "ClientResultResponse":
        return ClientResultResponse(
            client_id=dto.client_id, name=dto.name, trade_name=dto.trade_name,
            totals=ResultTotalsResponse.from_dto(dto.totals),
        )


class DriverResultResponse(BaseModel):
    driver_id: uuid.UUID
    name: str
    trip_cost_realized: Decimal
    linked_cost_realized: Decimal
    totals: ResultTotalsResponse

    @staticmethod
    def from_dto(dto: DriverResultDTO) -> "DriverResultResponse":
        return DriverResultResponse(
            driver_id=dto.driver_id, name=dto.name, trip_cost_realized=dto.trip_cost_realized,
            linked_cost_realized=dto.linked_cost_realized, totals=ResultTotalsResponse.from_dto(dto.totals),
        )


class VehicleCostOriginResponse(BaseModel):
    accounts_payable_id: uuid.UUID
    origin: str
    maintenance_order_id: uuid.UUID | None
    value: Decimal
    accounting_period: date
    status: str

    @staticmethod
    def from_dto(dto: VehicleCostOriginDTO) -> "VehicleCostOriginResponse":
        return VehicleCostOriginResponse(
            accounts_payable_id=dto.accounts_payable_id, origin=dto.origin,
            maintenance_order_id=dto.maintenance_order_id, value=dto.value,
            accounting_period=dto.competencia, status=dto.status,
        )


class VehicleResultDetailResponse(BaseModel):
    result: VehicleResultResponse
    trips: list[TripResultResponse]
    cost_origins: list[VehicleCostOriginResponse]

    @staticmethod
    def from_dto(dto: VehicleResultDetailDTO) -> "VehicleResultDetailResponse":
        return VehicleResultDetailResponse(
            result=VehicleResultResponse.from_dto(dto.result),
            trips=[TripResultResponse.from_dto(t) for t in dto.trips],
            cost_origins=[VehicleCostOriginResponse.from_dto(c) for c in dto.cost_origins],
        )


class ClientInvoiceSummaryResponse(BaseModel):
    invoice_id: uuid.UUID
    invoice_number: str
    issue_date: date
    status: str
    total_value: Decimal
    trip_count: int

    @staticmethod
    def from_dto(dto: ClientInvoiceSummaryDTO) -> "ClientInvoiceSummaryResponse":
        return ClientInvoiceSummaryResponse(
            invoice_id=dto.invoice_id, invoice_number=dto.invoice_number, issue_date=dto.issue_date,
            status=dto.status, total_value=dto.total_value, trip_count=dto.trip_count,
        )


class ClientResultDetailResponse(BaseModel):
    result: ClientResultResponse
    trips: list[TripResultResponse]
    invoices: list[ClientInvoiceSummaryResponse]

    @staticmethod
    def from_dto(dto: ClientResultDetailDTO) -> "ClientResultDetailResponse":
        return ClientResultDetailResponse(
            result=ClientResultResponse.from_dto(dto.result),
            trips=[TripResultResponse.from_dto(t) for t in dto.trips],
            invoices=[ClientInvoiceSummaryResponse.from_dto(i) for i in dto.invoices],
        )


class DriverLinkedCostResponse(BaseModel):
    accounts_payable_id: uuid.UUID
    origin: str
    value: Decimal
    accounting_period: date
    status: str

    @staticmethod
    def from_dto(dto: DriverLinkedCostDTO) -> "DriverLinkedCostResponse":
        return DriverLinkedCostResponse(
            accounts_payable_id=dto.accounts_payable_id, origin=dto.origin, value=dto.value,
            accounting_period=dto.competencia, status=dto.status,
        )


class DriverResultDetailResponse(BaseModel):
    result: DriverResultResponse
    trips: list[TripResultResponse]
    linked_costs: list[DriverLinkedCostResponse]

    @staticmethod
    def from_dto(dto: DriverResultDetailDTO) -> "DriverResultDetailResponse":
        return DriverResultDetailResponse(
            result=DriverResultResponse.from_dto(dto.result),
            trips=[TripResultResponse.from_dto(t) for t in dto.trips],
            linked_costs=[DriverLinkedCostResponse.from_dto(c) for c in dto.linked_costs],
        )
