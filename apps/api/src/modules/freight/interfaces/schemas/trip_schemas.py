from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict

from modules.freight.application.dtos.trip_dto import TripDTO
from modules.tenancy.interfaces.schemas.tenant_schemas import AuditMetadataResponse


class TripReferencesResponse(BaseModel):
    client_id: uuid.UUID
    driver_id: uuid.UUID | None
    tractor_unit_id: uuid.UUID | None


class TripSnapshotsResponse(BaseModel):
    driver_name_snapshot: str | None
    tractor_unit_plate_snapshot: str | None
    client_snapshot: dict[str, Any] | None
    predicted_revenue_snapshot: Decimal | None
    applied_price_table_id: uuid.UUID | None
    applied_price_table_application_id: uuid.UUID | None


class TripCargoRouteResponse(BaseModel):
    origin_city: str | None
    origin_state: str | None
    destination_city: str | None
    destination_state: str | None
    predicted_distance_km: Decimal | None
    cargo_weight_kg: Decimal | None
    cargo_weight_tons: Decimal | None
    cargo_type: str | None
    cargo_quantity: int | None
    cargo_quantity_unit: str | None


class TripStatusResponse(BaseModel):
    operational: str
    fiscal: str
    financial: str
    closed: bool


class TripFinancialsResponse(BaseModel):
    predicted_cost: Decimal | None
    actual_cost: Decimal | None
    actual_revenue: Decimal | None
    predicted_margin: Decimal | None
    actual_margin: Decimal | None
    financial_deviation: Decimal | None


class TripResponse(BaseModel):
    id: uuid.UUID
    codigo: str
    scheduled_date: date | None
    scheduled_window: datetime | None
    references: TripReferencesResponse
    snapshots: TripSnapshotsResponse
    status: TripStatusResponse
    financials: TripFinancialsResponse
    cargo_route: TripCargoRouteResponse
    distance_traveled_km: Decimal | None
    audit: AuditMetadataResponse

    @staticmethod
    def from_dto(dto: TripDTO) -> "TripResponse":
        return TripResponse(
            id=dto.id,
            codigo=dto.codigo,
            scheduled_date=dto.data_programada,
            scheduled_window=dto.janela_programada,
            references=TripReferencesResponse(
                client_id=dto.cliente_id, driver_id=dto.motorista_id, tractor_unit_id=dto.veiculo_tracionador_id
            ),
            snapshots=TripSnapshotsResponse(
                driver_name_snapshot=dto.nome_motorista_snapshot,
                tractor_unit_plate_snapshot=dto.placa_veiculo_snapshot,
                client_snapshot=dto.cliente_snapshot,
                predicted_revenue_snapshot=dto.receita_prevista_snapshot,
                applied_price_table_id=dto.tabela_preco_aplicada_snapshot_id,
                applied_price_table_application_id=dto.aplicacao_tabela_preco_atual_id,
            ),
            status=TripStatusResponse(
                operational=dto.status_operacional, fiscal=dto.status_fiscal, financial=dto.status_financeiro,
                closed=dto.encerrada,
            ),
            financials=TripFinancialsResponse(
                predicted_cost=dto.custo_previsto,
                actual_cost=dto.custo_realizado,
                actual_revenue=dto.receita_realizada,
                predicted_margin=dto.margem_prevista,
                actual_margin=dto.margem_realizada,
                financial_deviation=dto.desvio_financeiro,
            ),
            cargo_route=TripCargoRouteResponse(
                origin_city=dto.origem_cidade, origin_state=dto.origem_uf, destination_city=dto.destino_cidade,
                destination_state=dto.destino_uf, predicted_distance_km=dto.distancia_prevista_km,
                cargo_weight_kg=dto.peso_carga_kg, cargo_weight_tons=dto.toneladas_carga,
                cargo_type=dto.tipo_carga, cargo_quantity=dto.quantidade_carga,
                cargo_quantity_unit=dto.unidade_quantidade_carga,
            ),
            distance_traveled_km=dto.km_rodado,
            audit=AuditMetadataResponse(
                created_at=dto.created_at, created_by=dto.created_by, updated_at=dto.updated_at, updated_by=dto.updated_by
            ),
        )


class CreateTripRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    cliente_id: uuid.UUID
    data_programada: date | None = None
    janela_programada: datetime | None = None


class UpdateTripRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    data_programada: date | None = None
    janela_programada: datetime | None = None
    origem_cidade: str | None = None
    origem_uf: str | None = None
    destino_cidade: str | None = None
    destino_uf: str | None = None
    distancia_prevista_km: Decimal | None = None
    peso_carga_kg: Decimal | None = None
    tipo_carga: str | None = None
    quantidade_carga: int | None = None
    unidade_quantidade_carga: str | None = None


class ApplyPriceTableRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    price_table_item_id: uuid.UUID
    base_percentual_valor: Decimal | None = None


class DispatchTripRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    # V1 Operational Hardening, Parte 2 — opcional: sem hodômetro na Viagem inteira, sem 2ª fonte
    # da verdade, `km_rodado` simplesmente fica indisponível depois (nunca estimado).
    departure_odometer_km: Decimal | None = None


class FinishTripRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    arrival_odometer_km: Decimal | None = None


class InterromperTripRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    notes: str


class CancelarTripRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    notes: str


class CloseAdministrativeTripRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    justification: str
