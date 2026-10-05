from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy.exc import IntegrityError

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError
from modules.documents.application.dtos.fiscal_configuration_dto import FiscalConfigurationDTO
from modules.documents.domain.entities.fiscal_configuration import FiscalConfiguration
from modules.documents.domain.value_objects.fiscal_configuration_environment import (
    FiscalConfigurationEnvironment,
)
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_fiscal_configuration_repository import (
    SqlAlchemyFiscalConfigurationRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor

_UNIQUE_TENANT_CONSTRAINT = "uq_configuracoes_fiscais_tenant_id"


@dataclass(frozen=True)
class CreateFiscalConfigurationCommand(Command):
    actor: AuthenticatedActor
    certificate_file_id: uuid.UUID
    certificate_expires_at: date
    environment: FiscalConfigurationEnvironment
    regime_tributario: str
    cte_series: str
    mdfe_series: str


class CreateFiscalConfigurationHandler(CommandHandler[CreateFiscalConfigurationCommand, FiscalConfigurationDTO]):
    """GAP P1 (Gate 6, descoberto validando o Hotfix P0 no TEST publicado) — `PATCH
    /configuracao-fiscal` sempre exigiu que a config já existisse (`UpdateFiscalConfigurationHandler`
    levanta `FISCAL_CONFIG_NOT_FOUND` se não houver uma), e nunca existiu nenhum caminho de criação
    inicial: um tenant novo não conseguia, sozinho, chegar ao primeiro despacho. `FiscalConfiguration
    .create()` (domínio) já existia pronto — nunca tinha sido exposto por nenhum Handler.

    Concorrência: diferente do `DispatchTripHandler` (Hotfix P0 Fase 2), aqui não há uma linha
    existente para `SELECT ... FOR UPDATE` travar na criação — a config ainda não existe. A defesa
    real contra duas criações concorrentes do mesmo tenant é a própria constraint do banco
    (`uq_configuracoes_fiscais_tenant_id`, D399/D110). A verificação `get_for_tenant()` abaixo só
    cobre o caso comum (fail-fast, sem round-trip extra de transação); a corrida genuína é resolvida
    deixando o `IntegrityError` da constraint subir do `commit()` e convertendo-o explicitamente em
    `409 FISCAL_CONFIG_ALREADY_EXISTS` — nunca um `500` cru vazando erro de SQL."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateFiscalConfigurationCommand) -> FiscalConfigurationDTO:
        config: FiscalConfiguration
        try:
            async with SQLAlchemyUnitOfWork() as uow:
                repo = SqlAlchemyFiscalConfigurationRepository(uow.session)

                if await repo.get_for_tenant() is not None:
                    raise ConflictError(
                        "FISCAL_CONFIG_ALREADY_EXISTS", "Configuração Fiscal já existe para este tenant."
                    )

                config = FiscalConfiguration.create(
                    certificado_arquivo_id=command.certificate_file_id,
                    certificado_validade=command.certificate_expires_at,
                    ambiente=command.environment,
                    regime_tributario=command.regime_tributario,
                    serie_cte=command.cte_series,
                    serie_mdfe=command.mdfe_series,
                )
                await repo.add(config)

                await self._audit.record(
                    uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="configuracoes_fiscais_tenant",
                    entidade_id=config.id, acao="CRIACAO", ator_id=command.actor.user_id,
                    ator_nome_snapshot=str(command.actor.user_id),
                )

                await uow.commit()
        except IntegrityError as exc:
            # `exc.orig` é o wrapper `AsyncAdapt_asyncpg_dbapi.IntegrityError` do SQLAlchemy — ele
            # mesmo não carrega `constraint_name`; quem carrega é `exc.orig.__cause__`, a exceção
            # `asyncpg.exceptions.UniqueViolationError` original (confirmado empiricamente, não por
            # suposição da API do driver).
            orig = getattr(exc, "orig", None)
            asyncpg_error = getattr(orig, "__cause__", None)
            constraint = getattr(asyncpg_error, "constraint_name", None)
            if constraint == _UNIQUE_TENANT_CONSTRAINT:
                raise ConflictError(
                    "FISCAL_CONFIG_ALREADY_EXISTS", "Configuração Fiscal já existe para este tenant."
                ) from exc
            raise

        return FiscalConfigurationDTO.from_entity(config)
