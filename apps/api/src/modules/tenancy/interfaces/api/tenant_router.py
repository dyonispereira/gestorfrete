from __future__ import annotations

from fastapi import APIRouter, Depends

from core.database.session import get_session_factory
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.tenancy.application.commands.update_tenant import UpdateTenantCommand, UpdateTenantHandler
from modules.tenancy.application.queries.get_tenant import GetTenantHandler, GetTenantQuery
from modules.tenancy.interfaces.schemas.tenant_schemas import TenantResponse, UpdateTenantRequest
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(tags=["Tenants"])


@router.get("/tenant", response_model=TenantResponse)
async def get_tenant(
    actor: AuthenticatedActor = Depends(require_permission("tenancy.company_data.view")),
) -> TenantResponse:
    handler = GetTenantHandler(get_session_factory())
    dto = await handler.handle(GetTenantQuery(actor=actor))
    return TenantResponse.from_dto(dto)


@router.patch("/tenant", response_model=TenantResponse)
async def update_tenant(
    body: UpdateTenantRequest,
    actor: AuthenticatedActor = Depends(require_permission("tenancy.company_data.edit")),
) -> TenantResponse:
    handler = UpdateTenantHandler()
    dto = await handler.handle(
        UpdateTenantCommand(actor=actor, razao_social=body.razao_social, cnpj=body.cnpj)
    )
    return TenantResponse.from_dto(dto)
