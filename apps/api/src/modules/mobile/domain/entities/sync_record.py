from __future__ import annotations

import uuid
from datetime import datetime

from shared_kernel.domain.base_entity import BaseEntity


class SyncRecord(BaseEntity[uuid.UUID]):
    """`registros_sincronizacao` — D135: registro de nível de lote (não de um comando isolado), D037
    imutável após criado."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        sessao_mobile_id: uuid.UUID,
        data_hora_inicio: datetime,
        data_hora_fim: datetime,
        quantidade_comandos: int,
        quantidade_sucesso: int,
        quantidade_falha: int,
    ) -> None:
        super().__init__(id)
        self.sessao_mobile_id = sessao_mobile_id
        self.data_hora_inicio = data_hora_inicio
        self.data_hora_fim = data_hora_fim
        self.quantidade_comandos = quantidade_comandos
        self.quantidade_sucesso = quantidade_sucesso
        self.quantidade_falha = quantidade_falha

    @classmethod
    def create(
        cls,
        *,
        sessao_mobile_id: uuid.UUID,
        started_at: datetime,
        finished_at: datetime,
        command_count: int,
        success_count: int,
        failure_count: int,
    ) -> "SyncRecord":
        return cls(
            id=uuid.uuid4(), sessao_mobile_id=sessao_mobile_id, data_hora_inicio=started_at,
            data_hora_fim=finished_at, quantidade_comandos=command_count, quantidade_sucesso=success_count,
            quantidade_falha=failure_count,
        )
