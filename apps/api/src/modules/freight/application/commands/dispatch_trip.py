from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.documents.application.commands.create_cte import CreateCteCommand, CreateCteHandler
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_fiscal_configuration_repository import (
    SqlAlchemyFiscalConfigurationRepository,
)
from modules.drivers.infrastructure.persistence.repositories.sqlalchemy_driver_repository import (
    SqlAlchemyDriverRepository,
)
from modules.fleet.application.availability_projector import VehicleAvailabilityProjector
from modules.fleet.application.trip_odometer_recorder import TripOdometerRecorder
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_repository import (
    SqlAlchemyVehicleRepository,
)
from modules.freight.application.dtos.trip_dto import TripDTO
from modules.freight.domain.entities.trip_status_history_entry import TripStatusHistoryEntry
from modules.freight.domain.value_objects.status_history_dimension import StatusHistoryDimension
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_allocation_repository import (
    SqlAlchemyTripAllocationRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_status_history_repository import (
    SqlAlchemyTripStatusHistoryRepository,
)
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from modules.notification_center.application.notification_dispatcher import NotificationDispatcher
from modules.notification_center.domain.value_objects.notification_channel import NotificationChannel
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class DispatchTripCommand(Command):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    origin: str  # 'portal_gestor' (commands/dispatch) ou 'app_motorista' (commands/start)
    hodometro_saida_km: Decimal | None = None


class DispatchTripHandler(CommandHandler[DispatchTripCommand, TripDTO]):
    """`commands/dispatch`/`commands/start` — mesma transição (`LIBERADA→EM_DESLOCAMENTO`), `origin`
    diferente gravado no histórico. D378 — momento em que `nome_motorista_snapshot`/
    `placa_veiculo_snapshot` são congelados pela primeira e única vez. D396 — toda Viagem
    despachada tem um CT-e correspondente.

    Hotfix P0 (Gate 6, incidente `VG-2026-6574BB`) — a criação do CT-e costumava rodar DEPOIS
    desta transação já ter commitado (`CreateCteHandler` abria sua própria UoW). Quando faltava
    `FiscalConfig` (ou qualquer outra falha ali), a Viagem já tinha transicionado
    `LIBERADA→EM_DESLOCAMENTO` de forma permanente e irreversível pela API normal — sem CT-e, sem
    caminho de retry (o domínio corretamente rejeita um segundo `dispatch()` a partir de
    `EM_DESLOCAMENTO`), e a `Idempotency-Key` da tentativa original era liberada pelo
    `IdempotencyStore` (a falha não deixa marca), então um retry com a mesma key batia num erro de
    domínio totalmente diferente do erro real. Agora: (1) `FiscalConfig` é validada ANTES de
    `trip.dispatch()` — fail-fast, nenhuma mutação em memória acontece se o pré-requisito não
    existir; (2) a criação do CT-e roda DENTRO desta mesma `uow`/transação, não mais como uma
    segunda transação separada — um único `uow.commit()` no final cobre Viagem + histórico +
    auditoria + CT-e + contador fiscal juntos. Qualquer falha em qualquer um desses passos causa
    rollback integral: a Viagem permanece `LIBERADA`, nenhum CT-e é persistido, e o contador
    `proximo_numero_cte` não é consumido (nunca decrementado/perdido em caso de falha).

    Os efeitos abaixo continuam DELIBERADAMENTE fora desta transação — não são obrigações legais
    como o CT-e, são projeções/dados derivados: `VehicleAvailabilityProjector.apply_trip_dispatched`
    é idempotente por design (`get_active` antes de `create`, sempre recomputa do zero a partir dos
    impedimentos ativos — uma falha aqui é segura para reconciliar depois) e
    `TripOdometerRecorder.record_departure` já é tratado como opcional pelo próprio domínio
    (`hodometro_saida_km` ausente é um caso normal, nunca estimado). Uma falha em qualquer um dos
    dois AINDA pode produzir "HTTP erro + Viagem despachada com sucesso" — risco residual
    conhecido e registrado como dívida arquitetural separada, fora do escopo deste hotfix."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()
        self._notifications = NotificationDispatcher()

    async def handle(self, command: DispatchTripCommand) -> TripDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            trip_repo = SqlAlchemyTripRepository(uow.session)
            history_repo = SqlAlchemyTripStatusHistoryRepository(uow.session)
            driver_repo = SqlAlchemyDriverRepository(uow.session)
            vehicle_repo = SqlAlchemyVehicleRepository(uow.session)
            user_repo = SqlAlchemyUserRepository(uow.session)
            allocation_repo = SqlAlchemyTripAllocationRepository(uow.session)
            fiscal_config_repo = SqlAlchemyFiscalConfigurationRepository(uow.session)

            trip = await trip_repo.get_by_id(command.trip_id)
            if trip is None:
                raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")

            # Fail-fast (Hotfix P0, Fase A): valida o pré-requisito fiscal ANTES de qualquer
            # mutação da Viagem. Não substitui a atomicidade da Fase B abaixo — só evita o caso
            # mais comum (config nunca cadastrada) sem sequer tocar a entidade em memória.
            if await fiscal_config_repo.get_for_tenant_locked() is None:
                raise NotFoundError("FISCAL_CONFIG_NOT_FOUND", "Configuração Fiscal do tenant não encontrada.")

            driver = await driver_repo.get_by_id(trip.motorista_id) if trip.motorista_id else None
            vehicle = await vehicle_repo.get_by_id(trip.veiculo_tracionador_id) if trip.veiculo_tracionador_id else None
            allocation = await allocation_repo.get_current_for_trip(trip.id)

            trip.dispatch(
                nome_motorista_snapshot=driver.nome if driver else "",
                placa_veiculo_snapshot=vehicle.placa if vehicle else "",
            )
            await trip_repo.add(trip)

            now = datetime.now(timezone.utc)
            await history_repo.add(
                TripStatusHistoryEntry.create(
                    viagem_id=trip.id,
                    dimensao=StatusHistoryDimension.OPERACIONAL,
                    status=trip.status_operacional.value,
                    usuario_id=command.actor.user_id,
                    origem=command.origin,
                    now=now,
                )
            )

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="viagens",
                entidade_id=trip.id,
                acao="TRANSICAO_STATUS",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"status_operacional": trip.status_operacional.value},
            )

            # D414 — `ViagemDespachada` notifica o Motorista alocado (link Motorista→Usuário já
            # provado no Lote 9/D408); nunca notifica o próprio ator (Motorista despachando a
            # própria Viagem via `commands/start`).
            if trip.motorista_id is not None:
                driver_user = await user_repo.get_by_driver_id_and_tenant(trip.motorista_id, command.actor.tenant_id)
                if driver_user is not None:
                    await self._notifications.notify(
                        uow.session, usuario_destinatario_id=driver_user.id, actor_user_id=command.actor.user_id,
                        canal=NotificationChannel.IN_APP, evento_origem_tipo="ViagemDespachada",
                        entidade_tipo="VIAGEM", entidade_id=trip.id, titulo="Viagem despachada",
                        mensagem=f"A viagem {trip.codigo} foi despachada e está pronta para deslocamento.", now=now,
                    )

            # Fase B — CT-e na MESMA transação: falha aqui reverte a Viagem também (rollback
            # integral via __aexit__ da própria `uow`, nenhum commit intermediário acontece).
            await CreateCteHandler().handle_in_transaction(
                CreateCteCommand(actor=command.actor, trip_id=trip.id), uow=uow
            )

            await uow.commit()

        if trip.veiculo_tracionador_id is not None:
            await VehicleAvailabilityProjector().apply_trip_dispatched(
                vehicle_id=trip.veiculo_tracionador_id, trip_id=trip.id, driver_id=trip.motorista_id,
                implement_id=allocation.implemento_id if allocation is not None else None, at=now,
            )

        if command.hodometro_saida_km is not None and trip.veiculo_tracionador_id is not None:
            await TripOdometerRecorder().record_departure(
                vehicle_id=trip.veiculo_tracionador_id, trip_id=trip.id, value_km=command.hodometro_saida_km, now=now,
            )

        return TripDTO.from_entity(trip)
