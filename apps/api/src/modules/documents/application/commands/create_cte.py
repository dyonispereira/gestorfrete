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
    """D396 — sem `POST /ctes`; único chamador é `DispatchTripHandler` (`freight`).

    Hotfix P0 (Gate 6, incidente `VG-2026-6574BB`) — antes deste handler abria sua própria
    `SQLAlchemyUnitOfWork` e comitava sozinho, DEPOIS do commit da Viagem já ter fechado a
    transação de `DispatchTripHandler`. Quando `FiscalConfig` estava ausente (ou qualquer outra
    falha aqui), a Viagem já tinha transicionado `LIBERADA→EM_DESLOCAMENTO` de forma permanente,
    sem CT-e correspondente e sem caminho de retry (o domínio corretamente rejeita um segundo
    `dispatch()` a partir de `EM_DESLOCAMENTO`). Agora recebe a `uow` já aberta por
    `DispatchTripHandler` — mesma sessão, mesma transação PostgreSQL, um único commit no
    chamador. Se qualquer passo aqui falhar, o rollback do `DispatchTripHandler` desfaz a
    transição da Viagem também: nunca mais existe um "CT-e obrigatório" pendente sem a Viagem
    correspondente, nem uma Viagem despachada sem CT-e."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateCteCommand) -> CteDTO:
        """Implementação da interface `CommandHandler` — abre e comita sua própria transação.
        Não é mais chamada por `DispatchTripHandler` (usa `handle_in_transaction`, Hotfix P0);
        preservada para qualquer uso futuro standalone/desacoplado do CT-e em relação ao despacho,
        sem quebrar a assinatura `handle(command) -> result` que o resto da base assume
        (`mypy --strict` rejeita um parâmetro extra aqui por violar Liskov)."""
        async with SQLAlchemyUnitOfWork() as uow:
            result = await self.handle_in_transaction(command, uow=uow)
            await uow.commit()
        return result

    async def handle_in_transaction(self, command: CreateCteCommand, *, uow: SQLAlchemyUnitOfWork) -> CteDTO:
        """Núcleo real — não abre nem comita nenhuma transação própria, o chamador é responsável
        pelo commit/rollback. É isto que `DispatchTripHandler` usa para que Viagem+CT-e sejam
        atômicos na mesma `uow`/sessão."""
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

        return CteDTO.from_entity(cte)
