from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from modules.fleet.domain.value_objects.impediment_type import ImpedimentoTipo


@dataclass(frozen=True)
class VehicleImpediment:
    """`veiculo_impedimentos` — ledger interno de `fleet` (não Read Model público, sem router/
    schema/permissão própria). `disponibilidade_veiculo` (D081/D247) deixa de ser um status
    sobrescrito pelo último evento e passa a ser uma projeção deste ledger: enquanto existir ao
    menos um registro com `encerrado_em IS NULL` para o veículo, ele está impedido — encerrar um
    impedimento nunca libera o veículo se outro ainda estiver ativo. `referencia_id` aponta para
    uma Viagem ou uma Ordem de Serviço (sem FK física — referência polimórfica, mesmo padrão já
    usado em `ordens_servico.origem_abertura`/Checklist)."""

    id: uuid.UUID
    veiculo_tracionador_id: uuid.UUID
    tipo: ImpedimentoTipo
    referencia_id: uuid.UUID
    motorista_id: uuid.UUID | None
    implemento_id: uuid.UUID | None
    iniciado_em: datetime
    encerrado_em: datetime | None

    @classmethod
    def create(
        cls,
        *,
        veiculo_tracionador_id: uuid.UUID,
        tipo: ImpedimentoTipo,
        referencia_id: uuid.UUID,
        motorista_id: uuid.UUID | None,
        implemento_id: uuid.UUID | None,
        now: datetime,
    ) -> "VehicleImpediment":
        return cls(
            id=uuid.uuid4(), veiculo_tracionador_id=veiculo_tracionador_id, tipo=tipo,
            referencia_id=referencia_id, motorista_id=motorista_id, implemento_id=implemento_id,
            iniciado_em=now, encerrado_em=None,
        )
