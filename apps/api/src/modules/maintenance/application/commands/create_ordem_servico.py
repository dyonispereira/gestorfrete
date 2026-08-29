from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from modules.fleet.application.availability_projector import VehicleAvailabilityProjector
from modules.fleet.application.commands.register_odometer_reading import (
    RegisterOdometerReadingCommand,
    RegisterOdometerReadingHandler,
)
from modules.fleet.domain.value_objects.odometer_origin import OdometerOrigin
from modules.maintenance.application.dtos.ordem_servico_dto import OrdemServicoDTO
from modules.maintenance.domain.entities.ordem_servico import OrdemServico
from modules.maintenance.domain.entities.ordem_servico_status_history_entry import OrdemServicoStatusHistoryEntry
from modules.maintenance.domain.value_objects.ordem_servico_origem_abertura import OrdemServicoOrigemAbertura
from modules.maintenance.domain.value_objects.ordem_servico_tipo import OrdemServicoTipo
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_ordem_servico_repository import (
    SqlAlchemyOrdemServicoRepository,
)
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_ordem_servico_status_history_repository import (
    SqlAlchemyOrdemServicoStatusHistoryRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateOrdemServicoCommand(Command):
    actor: AuthenticatedActor
    veiculo_tracionador_id: uuid.UUID
    tipo: str
    descricao_problema: str
    composicao_veicular_id: uuid.UUID | None = None
    fornecedor_executor_id: uuid.UUID | None = None
    origem_abertura: str = "MANUAL"
    hodometro_abertura_km: Decimal | None = None


class CreateOrdemServicoHandler(CommandHandler[CreateOrdemServicoCommand, OrdemServicoDTO]):
    """Nasce `ABERTA`. `origem_abertura` default `MANUAL` — o valor `CHECKLIST_REPROVADO` é usado
    só pelo gatilho automático em `reject_checklist.py`, nunca escolhido livremente pelo usuário.
    Após o commit, dois efeitos cross-module em `fleet` (mesmo padrão de D390/D398 — cada um sua
    própria UoW, não atômico com a OS): a disponibilidade do veículo vira `EM_MANUTENCAO`
    (`VehicleAvailabilityProjector`, scaffolding pré-existente desde a fundação de `fleet`, D247,
    nunca antes conectado); e, quando informado, o hodômetro de abertura vira uma Leitura de
    Hodômetro real (`origem=ORDEM_SERVICO`), sujeita ao invariante "nunca decresce" (D365) — se a
    leitura for rejeitada, a OS já foi criada, só a leitura falha (mesma característica aceita em
    todo cross-module síncrono deste código, ex. `documents.cancel_cte` → `freight`)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateOrdemServicoCommand) -> OrdemServicoDTO:
        now = datetime.now(timezone.utc)
        async with SQLAlchemyUnitOfWork() as uow:
            os_repo = SqlAlchemyOrdemServicoRepository(uow.session)
            history_repo = SqlAlchemyOrdemServicoStatusHistoryRepository(uow.session)

            ordem_servico = OrdemServico.create(
                veiculo_tracionador_id=command.veiculo_tracionador_id,
                composicao_veicular_id=command.composicao_veicular_id,
                fornecedor_executor_id=command.fornecedor_executor_id, tipo=OrdemServicoTipo(command.tipo),
                origem_abertura=OrdemServicoOrigemAbertura(command.origem_abertura),
                descricao_problema=command.descricao_problema, hodometro_abertura_km=command.hodometro_abertura_km,
                criado_por=command.actor.user_id, now=now,
            )
            await os_repo.add(ordem_servico)
            await history_repo.add(
                OrdemServicoStatusHistoryEntry.create(
                    ordem_servico_id=ordem_servico.id, status=ordem_servico.status.value,
                    usuario_id=command.actor.user_id, origem="usuario", now=now,
                )
            )
            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="ordens_servico",
                entidade_id=ordem_servico.id, acao="CRIACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"tipo": ordem_servico.tipo.value, "veiculo_tracionador_id": str(command.veiculo_tracionador_id)},
            )
            await uow.commit()

        await VehicleAvailabilityProjector().apply_service_order_opened(
            vehicle_id=ordem_servico.veiculo_tracionador_id, work_order_id=ordem_servico.id, at=now
        )
        if command.hodometro_abertura_km is not None:
            await RegisterOdometerReadingHandler().handle(
                RegisterOdometerReadingCommand(
                    actor=command.actor, vehicle_id=ordem_servico.veiculo_tracionador_id,
                    value_km=command.hodometro_abertura_km, origin=OdometerOrigin.ORDEM_SERVICO, trip_id=None,
                )
            )

        return OrdemServicoDTO.from_entity(ordem_servico)
