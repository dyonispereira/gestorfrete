from __future__ import annotations

import uuid
from decimal import Decimal

from modules.fleet.domain.value_objects.fuel_type import FuelType
from shared_kernel.domain.base_entity import BaseEntity


class VehicleTechnicalSheet(BaseEntity[uuid.UUID]):
    """Não-Aggregate-Root — 1:1 com `Vehicle`, Repository próprio (RBAC dedicado,
    `fleet.vehicle_technical_sheet.*`). Sem `criado_em`/`atualizado_em` — a DDL
    (`fichas_tecnicas_veiculo`) não tem essas colunas (`VEHICLE_IMPLEMENTATION.md`)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        veiculo_tracionador_id: uuid.UUID,
        chassi: str,
        motor: str | None,
        eixos: int,
        tara: Decimal,
        capacidade_carga: Decimal,
        pbt: Decimal,
        rntrc_proprietario: str | None,
        combustivel: FuelType,
    ) -> None:
        super().__init__(id)
        self.veiculo_tracionador_id = veiculo_tracionador_id
        self.chassi = chassi
        self.motor = motor
        self.eixos = eixos
        self.tara = tara
        self.capacidade_carga = capacidade_carga
        self.pbt = pbt
        self.rntrc_proprietario = rntrc_proprietario
        self.combustivel = combustivel

    @classmethod
    def create(
        cls,
        *,
        veiculo_tracionador_id: uuid.UUID,
        chassi: str,
        motor: str | None,
        eixos: int,
        tara: Decimal,
        capacidade_carga: Decimal,
        pbt: Decimal,
        rntrc_proprietario: str | None,
        combustivel: FuelType,
    ) -> "VehicleTechnicalSheet":
        return cls(
            id=uuid.uuid4(),
            veiculo_tracionador_id=veiculo_tracionador_id,
            chassi=chassi,
            motor=motor,
            eixos=eixos,
            tara=tara,
            capacidade_carga=capacidade_carga,
            pbt=pbt,
            rntrc_proprietario=rntrc_proprietario,
            combustivel=combustivel,
        )

    def update(
        self,
        *,
        chassi: str | None,
        motor: str | None,
        eixos: int | None,
        tara: Decimal | None,
        capacidade_carga: Decimal | None,
        pbt: Decimal | None,
        rntrc_proprietario: str | None,
        combustivel: FuelType | None,
    ) -> None:
        if chassi is not None:
            self.chassi = chassi
        if motor is not None:
            self.motor = motor
        if eixos is not None:
            self.eixos = eixos
        if tara is not None:
            self.tara = tara
        if capacidade_carga is not None:
            self.capacidade_carga = capacidade_carga
        if pbt is not None:
            self.pbt = pbt
        if rntrc_proprietario is not None:
            self.rntrc_proprietario = rntrc_proprietario
        if combustivel is not None:
            self.combustivel = combustivel
