from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import DomainError, NotFoundError
from modules.fleet.application.availability_projector import VehicleAvailabilityProjector
from modules.fleet.application.commands.register_odometer_reading import (
    RegisterOdometerReadingCommand,
    RegisterOdometerReadingHandler,
)
from modules.fleet.domain.value_objects.odometer_origin import OdometerOrigin
from modules.maintenance.application.dtos.ordem_servico_dto import OrdemServicoDTO
from modules.maintenance.domain.entities.ordem_servico_status_history_entry import OrdemServicoStatusHistoryEntry
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_item_ordem_servico_repository import (
    SqlAlchemyItemOrdemServicoRepository,
)
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_ordem_servico_repository import (
    SqlAlchemyOrdemServicoRepository,
)
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_ordem_servico_status_history_repository import (
    SqlAlchemyOrdemServicoStatusHistoryRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ConcluirOrdemServicoCommand(Command):
    actor: AuthenticatedActor
    ordem_servico_id: uuid.UUID
    hodometro_conclusao_km: Decimal | None = None


class ConcluirOrdemServicoHandler(CommandHandler[ConcluirOrdemServicoCommand, OrdemServicoDTO]):
    """`EM_EXECUCAO→CONCLUIDA`. Exige ao menos um item (D005/D006 — uma OS sem nenhum item
    executado não tem o que concluir). `custo_realizado` é congelado aqui com a soma dos itens no
    momento da conclusão — nenhum item pode ser adicionado depois (ver `create_item_ordem_servico.
    py`). Após o commit, dois efeitos cross-module em `fleet` (mesma característica de
    `create_ordem_servico.py`): veículo volta a `DISPONIVEL` (`003-MANUTENCAO.md` — "reparo
    finalizado, veículo testado e liberado para fleet" acontece em `CONCLUIDA`, não em `FECHADA`,
    que pode levar dias administrativos a mais); e, quando informado, o hodômetro de conclusão vira
    Leitura de Hodômetro real (`origem=ORDEM_SERVICO`)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: ConcluirOrdemServicoCommand) -> OrdemServicoDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            os_repo = SqlAlchemyOrdemServicoRepository(uow.session)
            history_repo = SqlAlchemyOrdemServicoStatusHistoryRepository(uow.session)
            item_repo = SqlAlchemyItemOrdemServicoRepository(uow.session)

            ordem_servico = await os_repo.get_by_id(command.ordem_servico_id)
            if ordem_servico is None:
                raise NotFoundError("MAINTENANCE_WORK_ORDER_NOT_FOUND", "Ordem de Serviço não encontrada.")

            itens = await item_repo.list_for_ordem_servico(command.ordem_servico_id)
            if not itens:
                raise DomainError(
                    "MAINTENANCE_WORK_ORDER_NO_ITEMS", "Ordem de Serviço precisa de ao menos um item para ser concluída."
                )

            now = datetime.now(timezone.utc)
            total = sum((i.valor_total for i in itens), Decimal("0.00"))
            ordem_servico.recompute_custo_realizado(value=total)
            ordem_servico.concluir(
                hodometro_km=command.hodometro_conclusao_km, now=now, atualizado_por=command.actor.user_id
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
                entidade_id=ordem_servico.id, acao="TRANSICAO_STATUS", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"status": ordem_servico.status.value, "custo_realizado": str(total)},
            )
            await uow.commit()

        await VehicleAvailabilityProjector().apply_service_order_closed(
            vehicle_id=ordem_servico.veiculo_tracionador_id, work_order_id=ordem_servico.id, at=now
        )
        if command.hodometro_conclusao_km is not None:
            await RegisterOdometerReadingHandler().handle(
                RegisterOdometerReadingCommand(
                    actor=command.actor, vehicle_id=ordem_servico.veiculo_tracionador_id,
                    value_km=command.hodometro_conclusao_km, origin=OdometerOrigin.ORDEM_SERVICO, trip_id=None,
                )
            )

        return OrdemServicoDTO.from_entity(ordem_servico)
