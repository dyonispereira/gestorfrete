from __future__ import annotations

import uuid
from datetime import datetime

from core.exceptions.base import ConflictError
from modules.fleet.domain.value_objects.vehicle_status import VehicleStatus
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class Vehicle(BaseAggregateRoot[uuid.UUID]):
    """Aggregate Root de `fleet` — `docs/domain/003-frota.md` "Veículo Tracionador". `Ficha
    Técnica`/`Documento do Veículo`/`Leitura de Hodômetro` são filhos do agregado no Domain Model,
    mas lidos/salvos pelos próprios Repositories (`VEHICLE_IMPLEMENTATION.md`)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        codigo: str,
        placa: str,
        renavam: str,
        fabricante: str,
        modelo: str,
        ano_fabricacao: int,
        categoria_veiculo_id: uuid.UUID,
        filial_id: uuid.UUID | None,
        status: VehicleStatus,
        audit: AuditMetadata,
    ) -> None:
        super().__init__(id)
        self.codigo = codigo
        self.placa = placa
        self.renavam = renavam
        self.fabricante = fabricante
        self.modelo = modelo
        self.ano_fabricacao = ano_fabricacao
        self.categoria_veiculo_id = categoria_veiculo_id
        self.filial_id = filial_id
        self.status = status
        self.audit = audit

    @classmethod
    def create(
        cls,
        *,
        codigo: str,
        placa: str,
        renavam: str,
        fabricante: str,
        modelo: str,
        ano_fabricacao: int,
        categoria_veiculo_id: uuid.UUID,
        filial_id: uuid.UUID | None,
        audit: AuditMetadata,
    ) -> "Vehicle":
        return cls(
            id=uuid.uuid4(),
            codigo=codigo,
            placa=placa,
            renavam=renavam,
            fabricante=fabricante,
            modelo=modelo,
            ano_fabricacao=ano_fabricacao,
            categoria_veiculo_id=categoria_veiculo_id,
            filial_id=filial_id,
            status=VehicleStatus.ATIVO,
            audit=audit,
        )

    def update(
        self,
        *,
        fabricante: str | None,
        modelo: str | None,
        ano_fabricacao: int | None,
        categoria_veiculo_id: uuid.UUID | None,
        filial_id: uuid.UUID | None,
        updated_by: uuid.UUID,
        now: datetime,
    ) -> None:
        if fabricante is not None:
            self.fabricante = fabricante
        if modelo is not None:
            self.modelo = modelo
        if ano_fabricacao is not None:
            self.ano_fabricacao = ano_fabricacao
        if categoria_veiculo_id is not None:
            self.categoria_veiculo_id = categoria_veiculo_id
        if filial_id is not None:
            self.filial_id = filial_id
        self.audit = self.audit.touched(by=updated_by, at=now)

    def deactivate(self, *, deactivated_by: uuid.UUID, now: datetime) -> None:
        if self.audit.is_deleted:
            raise ConflictError("FLEET_VEHICLE_ALREADY_INACTIVE", "Veículo já está inativo.")
        self.status = VehicleStatus.INATIVO
        self.audit = self.audit.soft_deleted(by=deactivated_by, at=now)
