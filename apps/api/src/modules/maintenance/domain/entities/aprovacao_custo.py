from __future__ import annotations

import uuid
from datetime import datetime

from modules.maintenance.domain.value_objects.aprovacao_custo_decisao import AprovacaoCustoDecisao
from shared_kernel.domain.base_entity import BaseEntity


class AprovacaoCusto(BaseEntity[uuid.UUID]):
    """`aprovacoes_custo` — registro pontual, nunca alterado (D007/D010, decisão explícita).
    `nivel` preparado para workflow multi-nível futuro — sempre `1` nesta Lote."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        ordem_servico_id: uuid.UUID,
        nivel: int,
        decisao: AprovacaoCustoDecisao,
        justificativa: str | None,
        ator_id: uuid.UUID,
        data_hora: datetime,
    ) -> None:
        super().__init__(id)
        self.ordem_servico_id = ordem_servico_id
        self.nivel = nivel
        self.decisao = decisao
        self.justificativa = justificativa
        self.ator_id = ator_id
        self.data_hora = data_hora

    @classmethod
    def create(
        cls, *, ordem_servico_id: uuid.UUID, decisao: AprovacaoCustoDecisao, justificativa: str | None,
        ator_id: uuid.UUID, now: datetime,
    ) -> "AprovacaoCusto":
        return cls(
            id=uuid.uuid4(), ordem_servico_id=ordem_servico_id, nivel=1, decisao=decisao,
            justificativa=justificativa, ator_id=ator_id, data_hora=now,
        )
