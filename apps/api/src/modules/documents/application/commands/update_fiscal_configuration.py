from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.documents.application.dtos.fiscal_configuration_dto import FiscalConfigurationDTO
from modules.documents.domain.value_objects.fiscal_configuration_environment import (
    FiscalConfigurationEnvironment,
)
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_fiscal_configuration_repository import (
    SqlAlchemyFiscalConfigurationRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateFiscalConfigurationCommand(Command):
    actor: AuthenticatedActor
    regime_tributario: str | None
    certificate_file_id: uuid.UUID | None
    certificate_expires_at: date | None
    cte_series: str | None
    mdfe_series: str | None
    environment: FiscalConfigurationEnvironment | None


class UpdateFiscalConfigurationHandler(CommandHandler[UpdateFiscalConfigurationCommand, FiscalConfigurationDTO]):
    """D229 parcial, com quatro grupos de campo cada um exigindo sua própria permissão — a
    verificação de permissão por grupo acontece no Router (`interfaces/api`), nunca aqui; este
    Handler só aplica o que já foi autorizado a chegar no corpo do Command."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: UpdateFiscalConfigurationCommand) -> FiscalConfigurationDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyFiscalConfigurationRepository(uow.session)
            config = await repo.get_for_tenant()
            if config is None:
                raise NotFoundError("FISCAL_CONFIG_NOT_FOUND", "Configuração Fiscal do tenant não encontrada.")

            config.update(
                regime_tributario=command.regime_tributario, certificado_arquivo_id=command.certificate_file_id,
                certificado_validade=command.certificate_expires_at, serie_cte=command.cte_series,
                serie_mdfe=command.mdfe_series, ambiente=command.environment,
            )
            await repo.add(config)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="configuracoes_fiscais_tenant",
                entidade_id=config.id, acao="ALTERACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )
            await uow.commit()

        return FiscalConfigurationDTO.from_entity(config)
