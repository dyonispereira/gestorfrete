from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.documents.domain.entities.fiscal_configuration import FiscalConfiguration
from modules.documents.domain.repositories.fiscal_configuration_repository import FiscalConfigurationRepository
from modules.documents.domain.value_objects.fiscal_configuration_environment import (
    FiscalConfigurationEnvironment,
)
from modules.documents.domain.value_objects.fiscal_configuration_status import FiscalConfigurationStatus
from modules.documents.infrastructure.persistence.models.fiscal_configuration_model import (
    FiscalConfigurationModel,
)


def _to_entity(model: FiscalConfigurationModel) -> FiscalConfiguration:
    return FiscalConfiguration(
        id=model.id, certificado_arquivo_id=model.certificado_arquivo_id,
        certificado_validade=model.certificado_validade, ambiente=FiscalConfigurationEnvironment(model.ambiente),
        regime_tributario=model.regime_tributario, serie_cte=model.serie_cte,
        proximo_numero_cte=model.proximo_numero_cte, serie_mdfe=model.serie_mdfe,
        proximo_numero_mdfe=model.proximo_numero_mdfe, status=FiscalConfigurationStatus(model.status),
    )


class SqlAlchemyFiscalConfigurationRepository(FiscalConfigurationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_for_tenant(self) -> FiscalConfiguration | None:
        tenant_id = get_current_tenant_id()
        stmt = select(FiscalConfigurationModel).where(FiscalConfigurationModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def get_for_tenant_locked(self) -> FiscalConfiguration | None:
        tenant_id = get_current_tenant_id()
        stmt = (
            select(FiscalConfigurationModel)
            .where(FiscalConfigurationModel.tenant_id == tenant_id)
            .with_for_update()
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def add(self, configuration: FiscalConfiguration) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(FiscalConfigurationModel, configuration.id)
        if model is None:
            model = FiscalConfigurationModel(id=configuration.id, tenant_id=tenant_id)
            self._session.add(model)
        model.certificado_arquivo_id = configuration.certificado_arquivo_id
        model.certificado_validade = configuration.certificado_validade
        model.ambiente = configuration.ambiente.value
        model.regime_tributario = configuration.regime_tributario
        model.serie_cte = configuration.serie_cte
        model.proximo_numero_cte = configuration.proximo_numero_cte
        model.serie_mdfe = configuration.serie_mdfe
        model.proximo_numero_mdfe = configuration.proximo_numero_mdfe
        model.status = configuration.status.value
        await self._session.flush()
