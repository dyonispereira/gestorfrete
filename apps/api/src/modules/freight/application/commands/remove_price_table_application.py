from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_cte_repository import (
    SqlAlchemyCteRepository,
)
from modules.freight.application.dtos.trip_dto import TripDTO
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_price_application_repository import (
    SqlAlchemyTripPriceApplicationRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class RemovePriceTableApplicationCommand(Command):
    actor: AuthenticatedActor
    trip_id: uuid.UUID


class RemovePriceTableApplicationHandler(CommandHandler[RemovePriceTableApplicationCommand, TripDTO]):
    """Bloqueia a remoção se já existir QUALQUER CT-e para esta Viagem (`FISCAL_...` não, propositalmente
    `FREIGHT_TRIP_PRICE_REMOVAL_BLOCKED_BY_FISCAL`) — checagem real contra
    `documents.CteRepository.list_page(status=None)`, não contra `Trip.status_fiscal` (achado: esse
    campo nunca é transicionado pelo fluxo real de dispatch, só por simulação, D375). A linha em
    `aplicacoes_tabela_preco_viagem` nunca é apagada (D109-consistent), só marcada
    `removido_em`/`removido_por`, preservando a evidência da negociação desfeita."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: RemovePriceTableApplicationCommand) -> TripDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            trip_repo = SqlAlchemyTripRepository(uow.session)
            application_repo = SqlAlchemyTripPriceApplicationRepository(uow.session)

            trip = await trip_repo.get_by_id_for_update(command.trip_id)
            if trip is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")

            cte_repo = SqlAlchemyCteRepository(uow.session)
            _, cte_total = await cte_repo.list_page(
                page=1, limit=1, viagem_id=trip.id, status=None, serie=None, chave_acesso=None
            )
            if cte_total > 0:
                raise ConflictError(
                    "FREIGHT_TRIP_PRICE_REMOVAL_BLOCKED_BY_FISCAL",
                    "Não é possível remover a Tabela de Frete aplicada — esta Viagem já tem documento fiscal emitido.",
                )

            application_id = trip.aplicacao_tabela_preco_atual_id
            trip.remove_price_table_application()
            await trip_repo.add(trip)

            if application_id is not None:
                application = await application_repo.get_by_id(application_id)
                if application is not None:
                    now = datetime.now(timezone.utc)
                    application.remove(removed_by=command.actor.user_id, now=now)
                    await application_repo.mark_removed(application)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="viagens", entidade_id=trip.id,
                acao="ALTERACAO", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"tabela_preco_aplicada_snapshot_id": None},
            )

            await uow.commit()

        return TripDTO.from_entity(trip)
