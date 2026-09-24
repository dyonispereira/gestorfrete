from __future__ import annotations

import uuid
from datetime import datetime

from modules.fleet.domain.value_objects.vehicle_category_status import VehicleCategoryStatus
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class VehicleCategory(BaseAggregateRoot[uuid.UUID]):
    """Entidade de Referência (D036) — `docs/domain/003-frota.md` "Categoria de Veículo". Usada
    internamente por `Vehicle`/`Implement` (FK obrigatória).

    Reconciliado (V1 Operational Hardening, Parte 5): D363 fechado — `application`/`interfaces`
    própria implementadas (`RBAC_MATRIX.md` já tinha `fleet.vehicle_category.*` reservado desde
    antes). `codigo` é gerado internamente (mesmo padrão de `CostCenter.codigo`), nunca informado
    pelo usuário — só `nome`/`status` são atributos documentados no Data Dictionary."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        codigo: str,
        nome: str,
        status: VehicleCategoryStatus,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        super().__init__(id)
        self.codigo = codigo
        self.nome = nome
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def create(cls, *, codigo: str, nome: str, now: datetime) -> "VehicleCategory":
        return cls(
            id=uuid.uuid4(), codigo=codigo, nome=nome, status=VehicleCategoryStatus.ATIVA, created_at=now, updated_at=now
        )

    def update(self, *, nome: str | None, status: VehicleCategoryStatus | None, now: datetime) -> None:
        if nome is not None:
            self.nome = nome
        if status is not None:
            self.status = status
        self.updated_at = now
