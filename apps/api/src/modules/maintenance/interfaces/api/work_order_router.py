from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.maintenance.application.commands.aprovar_custo_ordem_servico import (
    AprovarCustoOrdemServicoCommand,
    AprovarCustoOrdemServicoHandler,
)
from modules.maintenance.application.commands.cancelar_ordem_servico import (
    CancelarOrdemServicoCommand,
    CancelarOrdemServicoHandler,
)
from modules.maintenance.application.commands.concluir_ordem_servico import (
    ConcluirOrdemServicoCommand,
    ConcluirOrdemServicoHandler,
)
from modules.maintenance.application.commands.create_item_ordem_servico import (
    CreateItemOrdemServicoCommand,
    CreateItemOrdemServicoHandler,
)
from modules.maintenance.application.commands.create_ordem_servico import (
    CreateOrdemServicoCommand,
    CreateOrdemServicoHandler,
)
from modules.maintenance.application.commands.diagnosticar_ordem_servico import (
    DiagnosticarOrdemServicoCommand,
    DiagnosticarOrdemServicoHandler,
)
from modules.maintenance.application.commands.fechar_ordem_servico import (
    FecharOrdemServicoCommand,
    FecharOrdemServicoHandler,
)
from modules.maintenance.application.commands.iniciar_execucao_ordem_servico import (
    IniciarExecucaoOrdemServicoCommand,
    IniciarExecucaoOrdemServicoHandler,
)
from modules.maintenance.application.commands.reprovar_custo_ordem_servico import (
    ReprovarCustoOrdemServicoCommand,
    ReprovarCustoOrdemServicoHandler,
)
from modules.maintenance.application.commands.submeter_aprovacao_ordem_servico import (
    SubmeterAprovacaoOrdemServicoCommand,
    SubmeterAprovacaoOrdemServicoHandler,
)
from modules.maintenance.application.queries.get_ordem_servico import GetOrdemServicoHandler, GetOrdemServicoQuery
from modules.maintenance.application.queries.list_aprovacoes_custo import (
    ListAprovacoesCustoHandler,
    ListAprovacoesCustoQuery,
)
from modules.maintenance.application.queries.list_itens_ordem_servico import (
    ListItensOrdemServicoHandler,
    ListItensOrdemServicoQuery,
)
from modules.maintenance.application.queries.list_ordem_servico_status_history import (
    ListOrdemServicoStatusHistoryHandler,
    ListOrdemServicoStatusHistoryQuery,
)
from modules.maintenance.application.queries.list_ordens_servico import ListOrdensServicoHandler, ListOrdensServicoQuery
from modules.maintenance.interfaces.schemas.work_order_schemas import (
    ApproveCostRequest,
    CancelWorkOrderRequest,
    CostApprovalResponse,
    CreateWorkOrderItemRequest,
    CreateWorkOrderRequest,
    DiagnoseWorkOrderRequest,
    RejectCostRequest,
    WorkOrderItemResponse,
    WorkOrderResponse,
    WorkOrderStatusHistoryEntryResponse,
)
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/ordens-servico", tags=["Work Orders"])


@router.get("")
async def list_work_orders(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    tractor_unit_id: uuid.UUID | None = None,
    type: str | None = None,
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("maintenance.work_order.view")),
) -> dict[str, Any]:
    handler = ListOrdensServicoHandler(get_session_factory())
    result = await handler.handle(
        ListOrdensServicoQuery(
            actor=actor, page=page, limit=limit, veiculo_tracionador_id=tractor_unit_id, tipo=type, status=status,
        )
    )
    return {
        "data": [WorkOrderResponse.from_dto(o) for o in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{work_order_id}", response_model=WorkOrderResponse)
async def get_work_order(
    work_order_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("maintenance.work_order.view"))
) -> WorkOrderResponse:
    handler = GetOrdemServicoHandler(get_session_factory())
    dto = await handler.handle(GetOrdemServicoQuery(actor=actor, ordem_servico_id=work_order_id))
    return WorkOrderResponse.from_dto(dto)


@router.post("", response_model=WorkOrderResponse, status_code=201)
async def create_work_order(
    body: CreateWorkOrderRequest, actor: AuthenticatedActor = Depends(require_permission("maintenance.work_order.create"))
) -> WorkOrderResponse:
    handler = CreateOrdemServicoHandler()
    dto = await handler.handle(
        CreateOrdemServicoCommand(
            actor=actor, veiculo_tracionador_id=body.tractor_unit_id, tipo=body.type,
            descricao_problema=body.problem_description, composicao_veicular_id=body.composition_id,
            fornecedor_executor_id=body.supplier_id,
        )
    )
    return WorkOrderResponse.from_dto(dto)


@router.post("/{work_order_id}/commands/diagnosticar", response_model=WorkOrderResponse)
async def diagnosticar_work_order(
    work_order_id: uuid.UUID, body: DiagnoseWorkOrderRequest,
    actor: AuthenticatedActor = Depends(require_permission("maintenance.work_order.edit")),
) -> WorkOrderResponse:
    handler = DiagnosticarOrdemServicoHandler()
    dto = await handler.handle(
        DiagnosticarOrdemServicoCommand(
            actor=actor, ordem_servico_id=work_order_id, diagnostico_tecnico=body.technical_diagnosis,
            causa=body.cause, causa_raiz=body.root_cause, mecanico_id=body.mechanic_id,
            necessita_aprovacao=body.needs_approval,
        )
    )
    return WorkOrderResponse.from_dto(dto)


@router.post("/{work_order_id}/commands/submeter-aprovacao", response_model=WorkOrderResponse)
async def submeter_aprovacao_work_order(
    work_order_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("maintenance.work_order.edit"))
) -> WorkOrderResponse:
    handler = SubmeterAprovacaoOrdemServicoHandler()
    dto = await handler.handle(SubmeterAprovacaoOrdemServicoCommand(actor=actor, ordem_servico_id=work_order_id))
    return WorkOrderResponse.from_dto(dto)


@router.post("/{work_order_id}/commands/aprovar-custo", response_model=WorkOrderResponse)
async def aprovar_custo_work_order(
    work_order_id: uuid.UUID, body: ApproveCostRequest,
    actor: AuthenticatedActor = Depends(require_permission("maintenance.work_order.approve_cost")),
) -> WorkOrderResponse:
    handler = AprovarCustoOrdemServicoHandler()
    dto = await handler.handle(
        AprovarCustoOrdemServicoCommand(actor=actor, ordem_servico_id=work_order_id, justificativa=body.justification)
    )
    return WorkOrderResponse.from_dto(dto)


@router.post("/{work_order_id}/commands/reprovar-custo", response_model=WorkOrderResponse)
async def reprovar_custo_work_order(
    work_order_id: uuid.UUID, body: RejectCostRequest,
    actor: AuthenticatedActor = Depends(require_permission("maintenance.work_order.reject_cost")),
) -> WorkOrderResponse:
    handler = ReprovarCustoOrdemServicoHandler()
    dto = await handler.handle(
        ReprovarCustoOrdemServicoCommand(actor=actor, ordem_servico_id=work_order_id, justificativa=body.justification)
    )
    return WorkOrderResponse.from_dto(dto)


@router.post("/{work_order_id}/commands/iniciar-execucao", response_model=WorkOrderResponse)
async def iniciar_execucao_work_order(
    work_order_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("maintenance.work_order.edit"))
) -> WorkOrderResponse:
    handler = IniciarExecucaoOrdemServicoHandler()
    dto = await handler.handle(IniciarExecucaoOrdemServicoCommand(actor=actor, ordem_servico_id=work_order_id))
    return WorkOrderResponse.from_dto(dto)


@router.post("/{work_order_id}/commands/concluir", response_model=WorkOrderResponse)
async def concluir_work_order(
    work_order_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("maintenance.work_order.edit"))
) -> WorkOrderResponse:
    handler = ConcluirOrdemServicoHandler()
    dto = await handler.handle(ConcluirOrdemServicoCommand(actor=actor, ordem_servico_id=work_order_id))
    return WorkOrderResponse.from_dto(dto)


@router.post("/{work_order_id}/commands/fechar", response_model=WorkOrderResponse)
async def fechar_work_order(
    work_order_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("maintenance.work_order.close"))
) -> WorkOrderResponse:
    handler = FecharOrdemServicoHandler()
    dto = await handler.handle(FecharOrdemServicoCommand(actor=actor, ordem_servico_id=work_order_id))
    return WorkOrderResponse.from_dto(dto)


@router.post("/{work_order_id}/commands/cancelar", response_model=WorkOrderResponse)
async def cancelar_work_order(
    work_order_id: uuid.UUID, body: CancelWorkOrderRequest,
    actor: AuthenticatedActor = Depends(require_permission("maintenance.work_order.cancel")),
) -> WorkOrderResponse:
    handler = CancelarOrdemServicoHandler()
    dto = await handler.handle(
        CancelarOrdemServicoCommand(actor=actor, ordem_servico_id=work_order_id, justificativa=body.justification)
    )
    return WorkOrderResponse.from_dto(dto)


@router.get("/{work_order_id}/status-history")
async def list_work_order_status_history(
    work_order_id: uuid.UUID,
    cursor: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("maintenance.work_order.view")),
) -> dict[str, Any]:
    handler = ListOrdemServicoStatusHistoryHandler(get_session_factory())
    result = await handler.handle(
        ListOrdemServicoStatusHistoryQuery(actor=actor, ordem_servico_id=work_order_id, cursor=cursor, limit=limit, status=status)
    )
    return {
        "data": [
            WorkOrderStatusHistoryEntryResponse(
                id=e.id, status=e.status, user_id=e.usuario_id, origin=e.origem, notes=e.observacao,
                occurred_at=e.data_hora,
            )
            for e in result.items
        ],
        "meta": {"pagination": {"next_cursor": result.next_cursor, "has_more": result.has_more}},
    }


@router.get("/{work_order_id}/itens")
async def list_work_order_items(
    work_order_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("maintenance.work_order_item.view"))
) -> dict[str, Any]:
    handler = ListItensOrdemServicoHandler(get_session_factory())
    items = await handler.handle(ListItensOrdemServicoQuery(actor=actor, ordem_servico_id=work_order_id))
    responses = [WorkOrderItemResponse.from_dto(i) for i in items]
    return {"data": responses, "meta": {"pagination": {"page": 1, "limit": len(responses), "total": len(responses)}}}


@router.post("/{work_order_id}/itens", response_model=WorkOrderItemResponse, status_code=201)
async def create_work_order_item(
    work_order_id: uuid.UUID, body: CreateWorkOrderItemRequest,
    actor: AuthenticatedActor = Depends(require_permission("maintenance.work_order_item.create")),
) -> WorkOrderItemResponse:
    handler = CreateItemOrdemServicoHandler()
    dto = await handler.handle(
        CreateItemOrdemServicoCommand(
            actor=actor, ordem_servico_id=work_order_id, categoria_custo=body.cost_category,
            descricao=body.description, quantidade=body.quantity, valor_unitario=body.unit_value,
            peca_estoque_id=body.part_stock_id,
        )
    )
    return WorkOrderItemResponse.from_dto(dto)


@router.get("/{work_order_id}/aprovacoes-custo")
async def list_work_order_cost_approvals(
    work_order_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("maintenance.work_order.view_cost"))
) -> dict[str, Any]:
    handler = ListAprovacoesCustoHandler(get_session_factory())
    aprovacoes = await handler.handle(ListAprovacoesCustoQuery(actor=actor, ordem_servico_id=work_order_id))
    responses = [CostApprovalResponse.from_dto(a) for a in aprovacoes]
    return {"data": responses, "meta": {"pagination": {"page": 1, "limit": len(responses), "total": len(responses)}}}
