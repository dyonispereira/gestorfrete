from __future__ import annotations

import uuid
from datetime import datetime

from core.exceptions.base import DomainError
from modules.fleet.domain.value_objects.combination_type import CombinationType
from modules.fleet.domain.value_objects.composition_status import CompositionStatus
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot

# D368 — placeholder ilustrativo, não a tabela CONTRAN real (`023-vehicle-compositions.md`
# registra o algoritmo exato como fora de escopo deste lote). Substituível sem quebrar o contrato
# HTTP quando Produto/Jurídico definir os valores oficiais.
_AXLE_RANGE_BY_COMBINATION_TYPE: dict[CombinationType, tuple[int, int]] = {
    CombinationType.SIMPLES: (2, 3),
    CombinationType.BITREM: (6, 9),
    CombinationType.RODOTREM: (7, 11),
}


class VehicleComposition(BaseAggregateRoot[uuid.UUID]):
    """Aggregate Root de `fleet` — `docs/domain/003-frota.md` "Composição Veicular". Vigência,
    nunca editada in-place (D248) — histórico é a própria tabela (D037,
    `COMPOSITION_IMPLEMENTATION.md`)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        veiculo_tracionador_id: uuid.UUID,
        tipo_combinacao: CombinationType,
        eixos_total: int,
        status: CompositionStatus,
        implementos: list[tuple[uuid.UUID, int]],
        data_inicio_vigencia: datetime,
        data_fim_vigencia: datetime | None,
        alterado_por: uuid.UUID | None,
    ) -> None:
        super().__init__(id)
        self.veiculo_tracionador_id = veiculo_tracionador_id
        self.tipo_combinacao = tipo_combinacao
        self.eixos_total = eixos_total
        self.status = status
        self.implementos = implementos
        self.data_inicio_vigencia = data_inicio_vigencia
        self.data_fim_vigencia = data_fim_vigencia
        self.alterado_por = alterado_por

    @staticmethod
    def check_axles(tipo_combinacao: CombinationType, eixos_total: int) -> None:
        minimum, maximum = _AXLE_RANGE_BY_COMBINATION_TYPE[tipo_combinacao]
        if not (minimum <= eixos_total <= maximum):
            raise DomainError(
                "FLEET_COMPOSITION_AXLES_MISMATCH",
                f"Total de eixos ({eixos_total}) incompatível com {tipo_combinacao.value} "
                f"(esperado entre {minimum} e {maximum}).",
            )

    @classmethod
    def create(
        cls,
        *,
        veiculo_tracionador_id: uuid.UUID,
        tipo_combinacao: CombinationType,
        eixos_total: int,
        implementos: list[tuple[uuid.UUID, int]],
        alterado_por: uuid.UUID,
        now: datetime,
    ) -> "VehicleComposition":
        cls.check_axles(tipo_combinacao, eixos_total)
        return cls(
            id=uuid.uuid4(),
            veiculo_tracionador_id=veiculo_tracionador_id,
            tipo_combinacao=tipo_combinacao,
            eixos_total=eixos_total,
            status=CompositionStatus.VALIDA,
            implementos=implementos,
            data_inicio_vigencia=now,
            data_fim_vigencia=None,
            alterado_por=alterado_por,
        )

    def end_validity(self, *, ended_by: uuid.UUID, now: datetime) -> None:
        """Nunca exposto como endpoint isolado — só chamado internamente por
        `CreateVehicleCompositionHandler` antes de inserir uma nova composição vigente para o
        mesmo veículo (D248, `COMPOSITION_IMPLEMENTATION.md`)."""

        if self.data_fim_vigencia is not None:
            raise DomainError("FLEET_COMPOSITION_ALREADY_ENDED", "Composição já não está vigente.")
        self.data_fim_vigencia = now
        self.alterado_por = ended_by

    def validate(self, *, is_valid: bool, validated_by: uuid.UUID) -> None:
        self.status = CompositionStatus.VALIDA if is_valid else CompositionStatus.INVALIDA
        self.alterado_por = validated_by
