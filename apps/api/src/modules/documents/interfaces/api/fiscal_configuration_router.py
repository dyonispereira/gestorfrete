from __future__ import annotations

from fastapi import APIRouter, Depends

from core.database.session import get_session_factory
from core.exceptions.base import AuthorizationError
from interfaces.dependencies.auth import get_current_actor
from modules.documents.application.commands.create_fiscal_configuration import (
    CreateFiscalConfigurationCommand,
    CreateFiscalConfigurationHandler,
)
from modules.documents.application.commands.update_fiscal_configuration import (
    UpdateFiscalConfigurationCommand,
    UpdateFiscalConfigurationHandler,
)
from modules.documents.application.queries.get_fiscal_configuration import (
    GetFiscalConfigurationHandler,
    GetFiscalConfigurationQuery,
)
from modules.documents.domain.value_objects.fiscal_configuration_environment import (
    FiscalConfigurationEnvironment,
)
from modules.documents.interfaces.schemas.fiscal_configuration_schemas import (
    CreateFiscalConfigurationRequest,
    FiscalConfigurationResponse,
    UpdateFiscalConfigurationRequest,
)
from modules.identity_access.application.authorization_service import AuthorizationService
from modules.identity_access.interfaces.dependencies.authorization import (
    get_authorization_service,
    require_permission,
)
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/configuracao-fiscal", tags=["Fiscal Configuration"])

# D267-style — cada grupo de campo de `PATCH /configuracao-fiscal` exige sua própria permissão
# (045-configuracao-fiscal.md). Enviar um campo sem a permissão correspondente rejeita a requisição
# inteira (D218-style rigor), nunca um PATCH parcialmente aplicado.
_FIELD_PERMISSIONS: dict[str, str] = {
    "tax_regime": "documents.fiscal_config.edit",
    "certificate_file_id": "documents.fiscal_config.manage_certificate",
    "certificate_expires_at": "documents.fiscal_config.manage_certificate",
    "cte_series": "documents.fiscal_config.manage_series",
    "mdfe_series": "documents.fiscal_config.manage_series",
    "environment": "documents.fiscal_config.switch_environment",
}


@router.get("", response_model=FiscalConfigurationResponse)
async def get_fiscal_configuration(
    actor: AuthenticatedActor = Depends(require_permission("documents.fiscal_config.view")),
) -> FiscalConfigurationResponse:
    handler = GetFiscalConfigurationHandler(get_session_factory())
    dto = await handler.handle(GetFiscalConfigurationQuery(actor=actor))
    return FiscalConfigurationResponse.from_dto(dto)


@router.post("", response_model=FiscalConfigurationResponse, status_code=201)
async def create_fiscal_configuration(
    body: CreateFiscalConfigurationRequest,
    actor: AuthenticatedActor = Depends(require_permission("documents.fiscal_config.edit")),
) -> FiscalConfigurationResponse:
    """GAP P1 (Gate 6) — criação inicial explícita, nunca um upsert do `PATCH`. Reutiliza
    `documents.fiscal_config.edit` (decisão aprovada: criar uma permissão `.create` dedicada
    exigiria migration de seed RBAC sem trazer separação de responsabilidade relevante para o
    piloto — o agregado é singular por tenant, `edit` já representa a autoridade de configurar os
    dados fiscais gerais)."""

    handler = CreateFiscalConfigurationHandler()
    dto = await handler.handle(
        CreateFiscalConfigurationCommand(
            actor=actor, certificate_file_id=body.certificate_file_id,
            certificate_expires_at=body.certificate_expires_at, environment=body.environment,
            regime_tributario=body.tax_regime, cte_series=body.cte_series, mdfe_series=body.mdfe_series,
        )
    )
    return FiscalConfigurationResponse.from_dto(dto)


@router.patch("", response_model=FiscalConfigurationResponse)
async def update_fiscal_configuration(
    body: UpdateFiscalConfigurationRequest,
    actor: AuthenticatedActor = Depends(get_current_actor),
    authz: AuthorizationService = Depends(get_authorization_service),
) -> FiscalConfigurationResponse:
    held = await authz.get_permission_codes(actor)
    provided_fields = body.model_dump(exclude_unset=True, exclude_none=True)
    for field_name in provided_fields:
        required_permission = _FIELD_PERMISSIONS[field_name]
        if required_permission not in held:
            raise AuthorizationError(
                "IDENTITY_PERMISSION_DENIED", f"Ação requer a permissão '{required_permission}'."
            )

    handler = UpdateFiscalConfigurationHandler()
    dto = await handler.handle(
        UpdateFiscalConfigurationCommand(
            actor=actor, regime_tributario=body.tax_regime, certificate_file_id=body.certificate_file_id,
            certificate_expires_at=body.certificate_expires_at, cte_series=body.cte_series,
            mdfe_series=body.mdfe_series,
            environment=FiscalConfigurationEnvironment(body.environment) if body.environment else None,
        )
    )
    return FiscalConfigurationResponse.from_dto(dto)
