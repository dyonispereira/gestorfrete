from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from modules.fleet.domain.value_objects.body_type import BodyType
from modules.fleet.domain.value_objects.implement_availability import ImplementAvailability
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class Implement(BaseAggregateRoot[uuid.UUID]):
    """Aggregate Root de `fleet` — `docs/domain/003-frota.md` "Implemento". Entidade independente,
    nunca um detalhe de Composição Veicular (D076, `IMPLEMENT_IMPLEMENTATION.md`). Sem
    `criado_por`/`atualizado_por`/`excluido_por` — a DDL (`implementos`) não os tem."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        codigo: str,
        placa: str,
        renavam: str,
        tipo_carroceria: BodyType,
        categoria_veiculo_id: uuid.UUID,
        capacidade_carga: Decimal,
        status_disponibilidade: ImplementAvailability,
        created_at: datetime,
        updated_at: datetime,
        deleted_at: datetime | None,
    ) -> None:
        super().__init__(id)
        self.codigo = codigo
        self.placa = placa
        self.renavam = renavam
        self.tipo_carroceria = tipo_carroceria
        self.categoria_veiculo_id = categoria_veiculo_id
        self.capacidade_carga = capacidade_carga
        self.status_disponibilidade = status_disponibilidade
        self.created_at = created_at
        self.updated_at = updated_at
        self.deleted_at = deleted_at

    @classmethod
    def create(
        cls,
        *,
        codigo: str,
        placa: str,
        renavam: str,
        tipo_carroceria: BodyType,
        categoria_veiculo_id: uuid.UUID,
        capacidade_carga: Decimal,
        now: datetime,
    ) -> "Implement":
        return cls(
            id=uuid.uuid4(),
            codigo=codigo,
            placa=placa,
            renavam=renavam,
            tipo_carroceria=tipo_carroceria,
            categoria_veiculo_id=categoria_veiculo_id,
            capacidade_carga=capacidade_carga,
            status_disponibilidade=ImplementAvailability.DISPONIVEL,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )

    def update(
        self,
        *,
        tipo_carroceria: BodyType | None,
        capacidade_carga: Decimal | None,
        status_disponibilidade: ImplementAvailability | None,
        now: datetime,
    ) -> None:
        if tipo_carroceria is not None:
            self.tipo_carroceria = tipo_carroceria
        if capacidade_carga is not None:
            self.capacidade_carga = capacidade_carga
        if status_disponibilidade is not None:
            self.status_disponibilidade = status_disponibilidade
        self.updated_at = now

    def soft_delete(self, *, now: datetime) -> None:
        self.status_disponibilidade = ImplementAvailability.INATIVO
        self.deleted_at = now
        self.updated_at = now
