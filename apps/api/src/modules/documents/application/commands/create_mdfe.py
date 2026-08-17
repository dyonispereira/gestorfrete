from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, ValidationError
from modules.documents.application.dtos.mdfe_dto import MdfeDTO
from modules.documents.domain.entities.mdfe import Mdfe
from modules.documents.domain.value_objects.cte_status import CteStatus
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_cte_repository import (
    SqlAlchemyCteRepository,
)
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_fiscal_configuration_repository import (
    SqlAlchemyFiscalConfigurationRepository,
)
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_mdfe_repository import (
    SqlAlchemyMdfeRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateMdfeCommand(Command):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    cte_ids: list[uuid.UUID]


class CreateMdfeHandler(CommandHandler[CreateMdfeCommand, MdfeDTO]):
    """`POST /mdfes` — diferente do CT-e, MDF-e nasce de um comando real: a decisão de quais CT-e
    consolidar é do Faturista."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateMdfeCommand) -> MdfeDTO:
        if not command.cte_ids:
            raise ConflictError("FISCAL_MDFE_NO_CTE", "cte_ids não pode ser vazio.")

        async with SQLAlchemyUnitOfWork() as uow:
            trip_repo = SqlAlchemyTripRepository(uow.session)
            cte_repo = SqlAlchemyCteRepository(uow.session)
            config_repo = SqlAlchemyFiscalConfigurationRepository(uow.session)
            mdfe_repo = SqlAlchemyMdfeRepository(uow.session)

            trip = await trip_repo.get_by_id(command.trip_id)
            if trip is None:
                raise ValidationError("FISCAL_UNKNOWN_TRIP_ID", "Viagem inexistente.")

            for cte_id in command.cte_ids:
                cte = await cte_repo.get_by_id(cte_id)
                if cte is None:
                    raise ValidationError("FISCAL_UNKNOWN_CTE_ID", "CT-e inexistente.")
                if cte.status != CteStatus.AUTORIZADO or cte.viagem_id != command.trip_id:
                    raise ConflictError(
                        "FISCAL_MDFE_CTE_NOT_AUTHORIZED", "Todo cte_id deve estar AUTORIZADO e pertencer à mesma Viagem."
                    )

            config = await config_repo.get_for_tenant_locked()
            if config is None:
                raise ValidationError("FISCAL_CONFIG_NOT_FOUND", "Configuração Fiscal do tenant não encontrada.")

            numero = str(config.reserve_next_mdfe_number())
            await config_repo.add(config)

            mdfe = Mdfe.create(viagem_id=command.trip_id, numero=numero, serie=config.serie_mdfe)
            await mdfe_repo.add(mdfe)
            for cte_id in command.cte_ids:
                await mdfe_repo.add_cte_link(mdfe.id, cte_id)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="mdfes", entidade_id=mdfe.id,
                acao="CRIACAO", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"numero": mdfe.numero, "cte_ids": [str(c) for c in command.cte_ids]},
            )
            await uow.commit()

        return MdfeDTO.from_entity(mdfe, cte_ids=command.cte_ids)
