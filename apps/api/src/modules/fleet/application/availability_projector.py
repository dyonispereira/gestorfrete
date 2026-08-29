from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from modules.fleet.domain.entities.vehicle_impediment import VehicleImpediment
from modules.fleet.domain.value_objects.availability_status import AvailabilityStatus
from modules.fleet.domain.value_objects.impediment_type import ImpedimentoTipo
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_availability_repository import (
    SqlAlchemyVehicleAvailabilityRepository,
)
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_impediment_repository import (
    SqlAlchemyVehicleImpedimentRepository,
)


class VehicleAvailabilityProjector:
    """A **única** forma de escrever em `disponibilidade_veiculo` em todo o código (D247,
    `AVAILABILITY_IMPLEMENTATION.md`) — não é um `CommandHandler`, não é acionável por HTTP, não
    existe schema de request para nenhum destes métodos.

    `disponibilidade_veiculo` deixou de ser um status sobrescrito pelo último evento — cada método
    abre/fecha um registro em `veiculo_impedimentos` (ledger interno, sem router próprio) e
    **recomputa** o status a partir do conjunto de impedimentos ainda ativos. Fechar um impedimento
    nunca libera o veículo se outro seguir aberto (ex.: Viagem em curso + OS aberta no mesmo
    veículo — concluir só a OS mantém `EM_VIAGEM`, nunca pula direto para `DISPONIVEL`). Prioridade
    de exibição quando mais de um tipo está ativo: `MANUTENCAO` sempre vence `VIAGEM` — um veículo
    na oficina não está dirigível, independente do estado da viagem. Nenhum estado novo foi criado
    (D247): a saída continua restrita a `DISPONIVEL`/`EM_VIAGEM`/`EM_MANUTENCAO` — `INATIVO` segue
    inalcançável, como já era antes desta mudança.

    `interromper`/`retomar` de Viagem (pane em rota) deliberadamente **não** fecham/reabrem o
    impedimento `VIAGEM` — o veículo continua "em viagem" tecnicamente, e se uma OS emergencial for
    aberta por cima, `MANUTENCAO` já assume a prioridade de exibição sem precisar de um terceiro
    tipo de impedimento."""

    async def apply_trip_dispatched(
        self, *, vehicle_id: uuid.UUID, trip_id: uuid.UUID, driver_id: uuid.UUID | None,
        implement_id: uuid.UUID | None, at: datetime,
    ) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            impediment_repo = SqlAlchemyVehicleImpedimentRepository(uow.session)
            existing = await impediment_repo.get_active(
                veiculo_tracionador_id=vehicle_id, tipo=ImpedimentoTipo.VIAGEM, referencia_id=trip_id
            )
            if existing is None:
                await impediment_repo.add(
                    VehicleImpediment.create(
                        veiculo_tracionador_id=vehicle_id, tipo=ImpedimentoTipo.VIAGEM, referencia_id=trip_id,
                        motorista_id=driver_id, implemento_id=implement_id, now=at,
                    )
                )
            await self._recompute(uow.session, vehicle_id=vehicle_id, now=at)
            await uow.commit()

    async def apply_trip_ended(self, *, vehicle_id: uuid.UUID, trip_id: uuid.UUID, at: datetime) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            impediment_repo = SqlAlchemyVehicleImpedimentRepository(uow.session)
            await impediment_repo.close(
                veiculo_tracionador_id=vehicle_id, tipo=ImpedimentoTipo.VIAGEM, referencia_id=trip_id, now=at
            )
            await self._recompute(uow.session, vehicle_id=vehicle_id, now=at)
            await uow.commit()

    async def apply_service_order_opened(self, *, vehicle_id: uuid.UUID, work_order_id: uuid.UUID, at: datetime) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            impediment_repo = SqlAlchemyVehicleImpedimentRepository(uow.session)
            existing = await impediment_repo.get_active(
                veiculo_tracionador_id=vehicle_id, tipo=ImpedimentoTipo.MANUTENCAO, referencia_id=work_order_id
            )
            if existing is None:
                await impediment_repo.add(
                    VehicleImpediment.create(
                        veiculo_tracionador_id=vehicle_id, tipo=ImpedimentoTipo.MANUTENCAO,
                        referencia_id=work_order_id, motorista_id=None, implemento_id=None, now=at,
                    )
                )
            await self._recompute(uow.session, vehicle_id=vehicle_id, now=at)
            await uow.commit()

    async def apply_service_order_closed(self, *, vehicle_id: uuid.UUID, work_order_id: uuid.UUID, at: datetime) -> None:
        async with SQLAlchemyUnitOfWork() as uow:
            impediment_repo = SqlAlchemyVehicleImpedimentRepository(uow.session)
            await impediment_repo.close(
                veiculo_tracionador_id=vehicle_id, tipo=ImpedimentoTipo.MANUTENCAO, referencia_id=work_order_id,
                now=at,
            )
            await self._recompute(uow.session, vehicle_id=vehicle_id, now=at)
            await uow.commit()

    @staticmethod
    async def _recompute(session: AsyncSession, *, vehicle_id: uuid.UUID, now: datetime) -> None:
        impediment_repo = SqlAlchemyVehicleImpedimentRepository(session)
        availability_repo = SqlAlchemyVehicleAvailabilityRepository(session)

        active = await impediment_repo.list_active(vehicle_id)
        manutencao = [i for i in active if i.tipo is ImpedimentoTipo.MANUTENCAO]
        viagem = [i for i in active if i.tipo is ImpedimentoTipo.VIAGEM]

        if manutencao:
            status, motorista_id, implemento_id = AvailabilityStatus.EM_MANUTENCAO, None, None
        elif viagem:
            latest = max(viagem, key=lambda i: i.iniciado_em)
            status, motorista_id, implemento_id = AvailabilityStatus.EM_VIAGEM, latest.motorista_id, latest.implemento_id
        else:
            status, motorista_id, implemento_id = AvailabilityStatus.DISPONIVEL, None, None

        await availability_repo.apply(
            veiculo_tracionador_id=vehicle_id, status=status, motorista_atual_id=motorista_id,
            implemento_atual_id=implemento_id, now=now,
        )
