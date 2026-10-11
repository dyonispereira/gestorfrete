from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.pricing.application.commands.activate_price_table import (
    ActivatePriceTableCommand,
    ActivatePriceTableHandler,
)
from modules.pricing.application.commands.create_price_table import CreatePriceTableCommand, CreatePriceTableHandler
from modules.pricing.application.commands.create_price_table_item import (
    CreatePriceTableItemCommand,
    CreatePriceTableItemHandler,
)
from modules.pricing.application.commands.delete_price_table_item import (
    DeletePriceTableItemCommand,
    DeletePriceTableItemHandler,
)
from modules.pricing.application.commands.expire_price_table import ExpirePriceTableCommand, ExpirePriceTableHandler
from modules.pricing.application.commands.update_price_table import UpdatePriceTableCommand, UpdatePriceTableHandler
from modules.pricing.application.queries.get_price_table import GetPriceTableHandler, GetPriceTableQuery
from modules.pricing.application.queries.list_price_table_items import (
    ListPriceTableItemsHandler,
    ListPriceTableItemsQuery,
)
from modules.pricing.application.queries.list_price_tables import ListPriceTablesHandler, ListPriceTablesQuery
from modules.pricing.interfaces.schemas.price_table_schemas import (
    CreatePriceTableItemRequest,
    CreatePriceTableRequest,
    PriceTableItemResponse,
    PriceTableResponse,
    UpdatePriceTableRequest,
)
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/tabelas-preco", tags=["Pricing"])


@router.get("")
async def list_price_tables(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    direcao: str | None = None,
    status: str | None = None,
    cliente_id: uuid.UUID | None = None,
    actor: AuthenticatedActor = Depends(require_permission("pricing.price_table.view")),
) -> dict[str, Any]:
    handler = ListPriceTablesHandler(get_session_factory())
    result = await handler.handle(
        ListPriceTablesQuery(
            actor=actor, page=page, limit=limit, direcao=direcao, status=status, cliente_id=cliente_id
        )
    )
    return {
        "data": [PriceTableResponse.from_dto(t) for t in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{price_table_id}", response_model=PriceTableResponse)
async def get_price_table(
    price_table_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("pricing.price_table.view")),
) -> PriceTableResponse:
    handler = GetPriceTableHandler(get_session_factory())
    dto = await handler.handle(GetPriceTableQuery(actor=actor, price_table_id=price_table_id))
    return PriceTableResponse.from_dto(dto)


@router.post("", response_model=PriceTableResponse, status_code=201)
async def create_price_table(
    body: CreatePriceTableRequest,
    actor: AuthenticatedActor = Depends(require_permission("pricing.price_table.create")),
) -> PriceTableResponse:
    handler = CreatePriceTableHandler()
    dto = await handler.handle(
        CreatePriceTableCommand(
            actor=actor, nome=body.nome, direcao=body.direcao, vigencia_inicio=body.vigencia_inicio,
            vigencia_fim=body.vigencia_fim, cliente_id=body.cliente_id,
        )
    )
    return PriceTableResponse.from_dto(dto)


@router.patch("/{price_table_id}", response_model=PriceTableResponse)
async def update_price_table(
    price_table_id: uuid.UUID,
    body: UpdatePriceTableRequest,
    actor: AuthenticatedActor = Depends(require_permission("pricing.price_table.edit")),
) -> PriceTableResponse:
    handler = UpdatePriceTableHandler()
    dto = await handler.handle(
        UpdatePriceTableCommand(
            actor=actor, price_table_id=price_table_id, nome=body.nome, vigencia_fim=body.vigencia_fim
        )
    )
    return PriceTableResponse.from_dto(dto)


@router.post("/{price_table_id}/commands/activate", response_model=PriceTableResponse)
async def activate_price_table(
    price_table_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("pricing.price_table.edit")),
) -> PriceTableResponse:
    handler = ActivatePriceTableHandler()
    dto = await handler.handle(ActivatePriceTableCommand(actor=actor, price_table_id=price_table_id))
    return PriceTableResponse.from_dto(dto)


@router.post("/{price_table_id}/commands/expire", response_model=PriceTableResponse)
async def expire_price_table(
    price_table_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("pricing.price_table.edit")),
) -> PriceTableResponse:
    handler = ExpirePriceTableHandler()
    dto = await handler.handle(ExpirePriceTableCommand(actor=actor, price_table_id=price_table_id))
    return PriceTableResponse.from_dto(dto)


@router.get("/{price_table_id}/itens")
async def list_price_table_items(
    price_table_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("pricing.price_table.view")),
) -> dict[str, Any]:
    handler = ListPriceTableItemsHandler(get_session_factory())
    items = await handler.handle(ListPriceTableItemsQuery(actor=actor, price_table_id=price_table_id))
    return {"data": [PriceTableItemResponse.from_dto(i) for i in items]}


@router.post("/{price_table_id}/itens", response_model=PriceTableItemResponse, status_code=201)
async def create_price_table_item(
    price_table_id: uuid.UUID,
    body: CreatePriceTableItemRequest,
    actor: AuthenticatedActor = Depends(require_permission("pricing.price_table.edit")),
) -> PriceTableItemResponse:
    handler = CreatePriceTableItemHandler()
    dto = await handler.handle(
        CreatePriceTableItemCommand(
            actor=actor, price_table_id=price_table_id, unidade_calculo=body.unidade_calculo,
            categoria_veiculo_id=body.categoria_veiculo_id, origem_uf=body.origem_uf, destino_uf=body.destino_uf,
            faixa_distancia_min_km=body.faixa_distancia_min_km, faixa_distancia_max_km=body.faixa_distancia_max_km,
            faixa_modo=body.faixa_modo, valor=body.valor, valor_minimo=body.valor_minimo,
            adicional_fixo=body.adicional_fixo, desconto_fixo=body.desconto_fixo,
            adicional_percentual=body.adicional_percentual, desconto_percentual=body.desconto_percentual,
            base_percentual_descricao=body.base_percentual_descricao,
        )
    )
    return PriceTableItemResponse.from_dto(dto)


@router.delete("/{price_table_id}/itens/{item_id}", status_code=204, response_model=None)
async def delete_price_table_item(
    price_table_id: uuid.UUID,
    item_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("pricing.price_table.edit")),
) -> None:
    handler = DeletePriceTableItemHandler()
    await handler.handle(DeletePriceTableItemCommand(actor=actor, price_table_id=price_table_id, item_id=item_id))
