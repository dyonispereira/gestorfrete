from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import DomainError, NotFoundError
from modules.freight.application.trip_internal_transitions import TripInternalTransitions
from modules.freight.domain.value_objects.trip_operational_status import TripOperationalStatus
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from modules.maintenance.application.dtos.checklist_dto import ChecklistDTO
from modules.maintenance.domain.entities.checklist import Checklist
from modules.maintenance.domain.entities.checklist_status_history_entry import ChecklistStatusHistoryEntry
from modules.maintenance.domain.value_objects.checklist_referencia_tipo import ChecklistReferenciaTipo
from modules.maintenance.domain.value_objects.checklist_type import ChecklistType
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_checklist_repository import (
    SqlAlchemyChecklistRepository,
)
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_checklist_status_history_repository import (
    SqlAlchemyChecklistStatusHistoryRepository,
)
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_ordem_servico_repository import (
    SqlAlchemyOrdemServicoRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateChecklistCommand(Command):
    actor: AuthenticatedActor
    tipo: str
    referencia_tipo: str
    referencia_id: uuid.UUID


class CreateChecklistHandler(CommandHandler[CreateChecklistCommand, ChecklistDTO]):
    """Nasce `PENDENTE`. Veículo/Motorista são snapshot da alocação vigente da referência no
    momento da criação (D038-style, não ressincronizam) — de uma Viagem (via alocação de recursos)
    ou de uma Ordem de Serviço (via `veiculo_tracionador_id` direto, sem motorista). Quando
    `TIPO=MOTORISTA_SAIDA` e `REFERENCIA_TIPO=VIAGEM`, é esta criação — não o preenchimento — que
    dispara `PLANEJADA→AGUARDANDO_CHECKLIST` (`007-CHECKLIST.md`). Chama o método
    `TripInternalTransitions.await_checklist` já existente em `freight` (D376) — sem alterar nada
    em `freight`."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateChecklistCommand) -> ChecklistDTO:
        tipo = ChecklistType(command.tipo)
        referencia_tipo = ChecklistReferenciaTipo(command.referencia_tipo)

        now = datetime.now(timezone.utc)
        should_await_checklist = False

        async with SQLAlchemyUnitOfWork() as uow:
            checklist_repo = SqlAlchemyChecklistRepository(uow.session)
            history_repo = SqlAlchemyChecklistStatusHistoryRepository(uow.session)

            if referencia_tipo is ChecklistReferenciaTipo.VIAGEM:
                trip_repo = SqlAlchemyTripRepository(uow.session)
                trip = await trip_repo.get_by_id(command.referencia_id)
                if trip is None:
                    raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")
                if trip.veiculo_tracionador_id is None:
                    raise DomainError(
                        "MAINTENANCE_CHECKLIST_TRIP_NOT_ALLOCATED",
                        "Viagem ainda não tem alocação de recursos — aloque motorista e veículo antes de criar o checklist.",
                    )
                should_await_checklist = (
                    tipo is ChecklistType.MOTORISTA_SAIDA and trip.status_operacional is TripOperationalStatus.PLANEJADA
                )
                veiculo_tracionador_id = trip.veiculo_tracionador_id
                motorista_id = trip.motorista_id
            else:
                os_repo = SqlAlchemyOrdemServicoRepository(uow.session)
                ordem_servico = await os_repo.get_by_id(command.referencia_id)
                if ordem_servico is None:
                    raise NotFoundError("MAINTENANCE_WORK_ORDER_NOT_FOUND", "Ordem de Serviço não encontrada.")
                veiculo_tracionador_id = ordem_servico.veiculo_tracionador_id
                motorista_id = None

            checklist = Checklist.create(
                tipo=tipo, referencia_tipo=referencia_tipo, referencia_id=command.referencia_id,
                veiculo_tracionador_id=veiculo_tracionador_id, motorista_id=motorista_id, now=now,
            )
            await checklist_repo.add(checklist)
            await history_repo.add(
                ChecklistStatusHistoryEntry.create(
                    checklist_id=checklist.id, status=checklist.status.value, usuario_id=command.actor.user_id,
                    origem="usuario", now=now,
                )
            )
            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="checklists", entidade_id=checklist.id,
                acao="CRIACAO", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"tipo": checklist.tipo.value, "referencia_id": str(checklist.referencia_id)},
            )
            await uow.commit()

        if should_await_checklist:
            await TripInternalTransitions().await_checklist(trip_id=command.referencia_id, now=datetime.now(timezone.utc))

        return ChecklistDTO.from_entity(checklist)
