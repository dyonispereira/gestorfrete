from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from modules.ai.domain.value_objects.inference_origin import InferenceOrigin
from modules.ai.domain.value_objects.inference_status import InferenceStatus
from shared_kernel.domain.base_entity import BaseEntity


class AIInference(BaseEntity[uuid.UUID]):
    """`inferencias_ia` (D172) — registro técnico, histórico (D037), nunca editado após executado.
    `modelo_ia_versao` é cópia fixa do `AIModel.versao` no momento da execução (D166/D169) — mudar a
    versão ativa do Modelo depois nunca altera esta cópia. `duracao_ms` é `GENERATED ALWAYS AS (...)
    STORED` no Postgres — nunca calculado aqui, sempre lido de volta do banco (mesmo padrão de
    `FiscalEvent.duracao_ms`, D382)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        tenant_id: uuid.UUID,
        modelo_ia_id: uuid.UUID,
        modelo_ia_versao: str,
        entrada: dict[str, Any],
        saida: dict[str, Any] | None,
        nivel_confianca: Decimal | None,
        data_hora_inicio: datetime,
        data_hora_fim: datetime | None,
        duracao_ms: int | None,
        custo: Decimal | None,
        numero_tentativa: int,
        origem: InferenceOrigin,
        status: InferenceStatus,
    ) -> None:
        super().__init__(id)
        self.tenant_id = tenant_id
        self.modelo_ia_id = modelo_ia_id
        self.modelo_ia_versao = modelo_ia_versao
        self.entrada = entrada
        self.saida = saida
        self.nivel_confianca = nivel_confianca
        self.data_hora_inicio = data_hora_inicio
        self.data_hora_fim = data_hora_fim
        self.duracao_ms = duracao_ms
        self.custo = custo
        self.numero_tentativa = numero_tentativa
        self.origem = origem
        self.status = status

    @classmethod
    def execute(
        cls, *, tenant_id: uuid.UUID, modelo_ia_id: uuid.UUID, modelo_ia_versao: str,
        entrada: dict[str, Any], saida: dict[str, Any] | None, nivel_confianca: Decimal | None,
        custo: Decimal | None, origem: InferenceOrigin, status: InferenceStatus, now: datetime,
    ) -> "AIInference":
        """D424 — `AIInferenceEngine` chama o `AIModelGateway` de forma síncrona: início e fim são o
        mesmo instante de execução do adapter (fake, determinístico nesta fundação)."""

        return cls(
            id=uuid.uuid4(), tenant_id=tenant_id, modelo_ia_id=modelo_ia_id, modelo_ia_versao=modelo_ia_versao,
            entrada=entrada, saida=saida, nivel_confianca=nivel_confianca, data_hora_inicio=now,
            data_hora_fim=now, duracao_ms=None, custo=custo, numero_tentativa=1, origem=origem, status=status,
        )
