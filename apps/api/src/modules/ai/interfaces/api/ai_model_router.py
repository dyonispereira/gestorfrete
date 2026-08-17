from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.ai.application.commands.create_ai_model import CreateAIModelCommand, CreateAIModelHandler
from modules.ai.application.commands.update_ai_model import UpdateAIModelCommand, UpdateAIModelHandler
from modules.ai.application.queries.get_ai_model import GetAIModelHandler, GetAIModelQuery
from modules.ai.application.queries.list_ai_models import ListAIModelsHandler, ListAIModelsQuery
from modules.ai.domain.value_objects.logical_provider import LogicalProvider
from modules.ai.domain.value_objects.model_status import ModelStatus
from modules.ai.domain.value_objects.model_type import ModelType
from modules.ai.interfaces.schemas.ai_model_schemas import (
    AIModelResponse,
    CreateAIModelRequest,
    UpdateAIModelRequest,
)
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/ai/models", tags=["AI Models"])


@router.get("")
async def list_ai_models(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    type: str | None = None,
    logical_provider: str | None = None,
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("ai.model.view")),
) -> dict[str, Any]:
    handler = ListAIModelsHandler(get_session_factory())
    result = await handler.handle(
        ListAIModelsQuery(
            actor=actor, page=page, limit=limit, type=type, logical_provider=logical_provider, status=status,
        )
    )
    return {
        "data": [AIModelResponse.from_dto(m) for m in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{model_id}", response_model=AIModelResponse)
async def get_ai_model(
    model_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("ai.model.view"))
) -> AIModelResponse:
    handler = GetAIModelHandler(get_session_factory())
    dto = await handler.handle(GetAIModelQuery(actor=actor, model_id=model_id))
    return AIModelResponse.from_dto(dto)


@router.post("", response_model=AIModelResponse, status_code=201)
async def create_ai_model(
    body: CreateAIModelRequest, actor: AuthenticatedActor = Depends(require_permission("ai.model.create"))
) -> AIModelResponse:
    handler = CreateAIModelHandler()
    dto = await handler.handle(
        CreateAIModelCommand(
            actor=actor, name=body.name, type=ModelType(body.type), version=body.version,
            logical_provider=LogicalProvider(body.logical_provider), capability=body.capability,
            max_context=body.max_context,
        )
    )
    return AIModelResponse.from_dto(dto)


@router.patch("/{model_id}", response_model=AIModelResponse)
async def update_ai_model(
    model_id: uuid.UUID, body: UpdateAIModelRequest,
    actor: AuthenticatedActor = Depends(require_permission("ai.model.edit")),
) -> AIModelResponse:
    handler = UpdateAIModelHandler()
    dto = await handler.handle(
        UpdateAIModelCommand(
            actor=actor, model_id=model_id, capability=body.capability, max_context=body.max_context,
            status=ModelStatus(body.status) if body.status is not None else None,
        )
    )
    return AIModelResponse.from_dto(dto)
