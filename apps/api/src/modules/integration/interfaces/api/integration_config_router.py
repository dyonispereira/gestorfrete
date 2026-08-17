from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.integration.application.commands.create_integration_config import (
    CreateIntegrationConfigCommand,
    CreateIntegrationConfigHandler,
)
from modules.integration.application.commands.set_integration_config_status import (
    DisableIntegrationConfigCommand,
    DisableIntegrationConfigHandler,
    EnableIntegrationConfigCommand,
    EnableIntegrationConfigHandler,
)
from modules.integration.application.commands.update_integration_config import (
    UpdateIntegrationConfigCommand,
    UpdateIntegrationConfigHandler,
)
from modules.integration.application.queries.get_integration_config import (
    GetIntegrationConfigHandler,
    GetIntegrationConfigQuery,
)
from modules.integration.application.queries.list_integration_configs import (
    ListIntegrationConfigsHandler,
    ListIntegrationConfigsQuery,
)
from modules.integration.interfaces.schemas.integration_config_schemas import (
    CreateIntegrationConfigRequest,
    IntegrationConfigResponse,
    UpdateIntegrationConfigRequest,
)
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/integrations", tags=["Integrations"])


@router.get("")
async def list_integration_configs(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    type: str | None = None,
    status: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("integration.config.view")),
) -> dict[str, Any]:
    handler = ListIntegrationConfigsHandler(get_session_factory())
    result = await handler.handle(
        ListIntegrationConfigsQuery(actor=actor, page=page, limit=limit, type=type, status=status)
    )
    return {
        "data": [IntegrationConfigResponse.from_dto(c) for c in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{config_id}", response_model=IntegrationConfigResponse)
async def get_integration_config(
    config_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("integration.config.view"))
) -> IntegrationConfigResponse:
    handler = GetIntegrationConfigHandler(get_session_factory())
    dto = await handler.handle(GetIntegrationConfigQuery(actor=actor, config_id=config_id))
    return IntegrationConfigResponse.from_dto(dto)


@router.post("", response_model=IntegrationConfigResponse, status_code=201)
async def create_integration_config(
    body: CreateIntegrationConfigRequest,
    actor: AuthenticatedActor = Depends(require_permission("integration.config.create")),
) -> IntegrationConfigResponse:
    handler = CreateIntegrationConfigHandler()
    dto = await handler.handle(
        CreateIntegrationConfigCommand(actor=actor, type=body.type, credential_file_id=body.credential_file_id)
    )
    return IntegrationConfigResponse.from_dto(dto)


@router.patch("/{config_id}", response_model=IntegrationConfigResponse)
async def update_integration_config(
    config_id: uuid.UUID, body: UpdateIntegrationConfigRequest,
    actor: AuthenticatedActor = Depends(require_permission("integration.config.edit")),
) -> IntegrationConfigResponse:
    handler = UpdateIntegrationConfigHandler()
    dto = await handler.handle(
        UpdateIntegrationConfigCommand(actor=actor, config_id=config_id, credential_file_id=body.credential_file_id)
    )
    return IntegrationConfigResponse.from_dto(dto)


@router.post("/{config_id}/commands/enable", response_model=IntegrationConfigResponse)
async def enable_integration_config(
    config_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("integration.config.enable"))
) -> IntegrationConfigResponse:
    handler = EnableIntegrationConfigHandler()
    dto = await handler.handle(EnableIntegrationConfigCommand(actor=actor, config_id=config_id))
    return IntegrationConfigResponse.from_dto(dto)


@router.post("/{config_id}/commands/disable", response_model=IntegrationConfigResponse)
async def disable_integration_config(
    config_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("integration.config.disable"))
) -> IntegrationConfigResponse:
    handler = DisableIntegrationConfigHandler()
    dto = await handler.handle(DisableIntegrationConfigCommand(actor=actor, config_id=config_id))
    return IntegrationConfigResponse.from_dto(dto)
