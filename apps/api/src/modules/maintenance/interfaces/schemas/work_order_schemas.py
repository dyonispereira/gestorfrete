from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from modules.maintenance.application.dtos.aprovacao_custo_dto import AprovacaoCustoDTO
from modules.maintenance.application.dtos.item_ordem_servico_dto import ItemOrdemServicoDTO
from modules.maintenance.application.dtos.ordem_servico_dto import OrdemServicoDTO
from modules.tenancy.interfaces.schemas.tenant_schemas import AuditMetadataResponse


class WorkOrderResponse(BaseModel):
    id: uuid.UUID
    codigo: str
    tractor_unit_id: uuid.UUID
    composition_id: uuid.UUID | None
    supplier_id: uuid.UUID | None
    type: str
    opening_origin: str
    problem_description: str
    cause: str | None
    root_cause: str | None
    technical_diagnosis: str | None
    mechanic_id: uuid.UUID | None
    predicted_cost: Decimal | None
    actual_cost: Decimal | None
    needs_approval: bool
    completion_evidence_required: bool
    status: str
    execution_started_at: datetime | None
    completed_at: datetime | None
    opening_odometer_km: Decimal | None
    completion_odometer_km: Decimal | None
    cost_center_id: uuid.UUID | None
    chart_of_accounts_id: uuid.UUID | None
    audit: AuditMetadataResponse

    @staticmethod
    def from_dto(dto: OrdemServicoDTO) -> "WorkOrderResponse":
        return WorkOrderResponse(
            id=dto.id, codigo=dto.codigo, tractor_unit_id=dto.veiculo_tracionador_id,
            composition_id=dto.composicao_veicular_id, supplier_id=dto.fornecedor_executor_id, type=dto.tipo,
            opening_origin=dto.origem_abertura, problem_description=dto.descricao_problema, cause=dto.causa,
            root_cause=dto.causa_raiz, technical_diagnosis=dto.diagnostico_tecnico, mechanic_id=dto.mecanico_id,
            predicted_cost=dto.custo_previsto, actual_cost=dto.custo_realizado, needs_approval=dto.necessita_aprovacao,
            completion_evidence_required=dto.evidencia_conclusao_exigida, status=dto.status,
            execution_started_at=dto.data_inicio_execucao, completed_at=dto.data_conclusao,
            opening_odometer_km=dto.hodometro_abertura_km, completion_odometer_km=dto.hodometro_conclusao_km,
            cost_center_id=dto.centro_custo_id, chart_of_accounts_id=dto.plano_contas_id,
            audit=AuditMetadataResponse(
                created_at=dto.criado_em, created_by=dto.criado_por, updated_at=dto.atualizado_em,
                updated_by=dto.atualizado_por,
            ),
        )


class CreateWorkOrderRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    tractor_unit_id: uuid.UUID
    type: str
    problem_description: str
    composition_id: uuid.UUID | None = None
    supplier_id: uuid.UUID | None = None
    opening_odometer_km: Decimal | None = None
    cost_center_id: uuid.UUID | None = None
    chart_of_accounts_id: uuid.UUID | None = None


class DiagnoseWorkOrderRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    technical_diagnosis: str | None = None
    cause: str | None = None
    root_cause: str | None = None
    mechanic_id: uuid.UUID | None = None
    needs_approval: bool = False


class ApproveCostRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    justification: str | None = None


class RejectCostRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    justification: str


class CancelWorkOrderRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    justification: str


class ConcludeWorkOrderRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    completion_odometer_km: Decimal | None = None


class WorkOrderItemResponse(BaseModel):
    id: uuid.UUID
    ordem_servico_id: uuid.UUID
    cost_category: str
    description: str
    part_stock_id: uuid.UUID | None
    quantity: Decimal
    unit_value: Decimal
    total_value: Decimal

    @staticmethod
    def from_dto(dto: ItemOrdemServicoDTO) -> "WorkOrderItemResponse":
        return WorkOrderItemResponse(
            id=dto.id, ordem_servico_id=dto.ordem_servico_id, cost_category=dto.categoria_custo,
            description=dto.descricao, part_stock_id=dto.peca_estoque_id, quantity=dto.quantidade,
            unit_value=dto.valor_unitario, total_value=dto.valor_total,
        )


class CreateWorkOrderItemRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    cost_category: str
    description: str
    quantity: Decimal
    unit_value: Decimal
    part_stock_id: uuid.UUID | None = None


class CostApprovalResponse(BaseModel):
    id: uuid.UUID
    ordem_servico_id: uuid.UUID
    level: int
    decision: str
    justification: str | None
    actor_id: uuid.UUID
    occurred_at: datetime

    @staticmethod
    def from_dto(dto: AprovacaoCustoDTO) -> "CostApprovalResponse":
        return CostApprovalResponse(
            id=dto.id, ordem_servico_id=dto.ordem_servico_id, level=dto.nivel, decision=dto.decisao,
            justification=dto.justificativa, actor_id=dto.ator_id, occurred_at=dto.data_hora,
        )


class WorkOrderStatusHistoryEntryResponse(BaseModel):
    id: uuid.UUID
    status: str
    user_id: uuid.UUID | None
    origin: str
    notes: str | None
    occurred_at: datetime
