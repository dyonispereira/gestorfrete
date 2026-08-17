from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.documents.application.dtos.cte_dto import CteDTO
from modules.documents.domain.entities.cte import Cte
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_cte_repository import (
    SqlAlchemyCteRepository,
)
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_fiscal_configuration_repository import (
    SqlAlchemyFiscalConfigurationRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateCteCommand(Command):
    actor: AuthenticatedActor
    trip_id: uuid.UUID


class CreateCteHandler(CommandHandler[CreateCteCommand, CteDTO]):
    """D396 — sem `POST /ctes`; único chamador é `DispatchTripHandler` (`freight`), logo após a
    Viagem transicionar `LIBERADA→EM_DESLOCAMENTO` (`ViagemDespachada`, `009-FISCAL.md`)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateCteCommand) -> CteDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            trip_repo = SqlAlchemyTripRepository(uow.session)
            config_repo = SqlAlchemyFiscalConfigurationRepository(uow.session)
            cte_repo = SqlAlchemyCteRepository(uow.session)

            trip = await trip_repo.get_by_id(command.trip_id)
            if trip is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")

            config = await config_repo.get_for_tenant_locked()
            if config is None:
                raise NotFoundError("FISCAL_CONFIG_NOT_FOUND", "Configuração Fiscal do tenant não encontrada.")

            numero = str(config.reserve_next_cte_number())
            await config_repo.add(config)

            now = datetime.now(timezone.utc)
            valor_servico: Decimal = trip.receita_prevista_snapshot or Decimal("0.00")
            cte = Cte.create(
                viagem_id=trip.id, numero=numero, serie=config.serie_cte, valor_servico=valor_servico, now=now
            )
            await cte_repo.add(cte)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="ctes", entidade_id=cte.id,
                acao="CRIACAO", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"numero": cte.numero, "serie": cte.serie},
            )

            await uow.commit()

        return CteDTO.from_entity(cte)
