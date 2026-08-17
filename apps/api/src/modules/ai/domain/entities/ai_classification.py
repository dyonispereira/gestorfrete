from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from modules.ai.domain.value_objects.classification_type import ClassificationType
from shared_kernel.domain.base_entity import BaseEntity


class AIClassification(BaseEntity[uuid.UUID]):
    """`classificacoes_ia` — rótulo pontual atribuído a uma entidade existente (Risco/Prioridade/
    Gravidade). Nunca dispara, por si só, uma ação em outro bounded context (D161) — puramente
    consultivo. Registro imutável: uma reclassificação é uma linha nova, a anterior permanece no
    histórico (D037)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        tenant_id: uuid.UUID,
        inferencia_ia_id: uuid.UUID,
        tipo_classificacao: ClassificationType,
        entidade_alvo_tipo: str,
        entidade_alvo_id: uuid.UUID,
        rotulo: str,
        nivel_confianca: Decimal,
        criado_em: datetime,
    ) -> None:
        super().__init__(id)
        self.tenant_id = tenant_id
        self.inferencia_ia_id = inferencia_ia_id
        self.tipo_classificacao = tipo_classificacao
        self.entidade_alvo_tipo = entidade_alvo_tipo
        self.entidade_alvo_id = entidade_alvo_id
        self.rotulo = rotulo
        self.nivel_confianca = nivel_confianca
        self.criado_em = criado_em

    @classmethod
    def create(
        cls, *, tenant_id: uuid.UUID, inferencia_ia_id: uuid.UUID, tipo_classificacao: ClassificationType,
        entidade_alvo_tipo: str, entidade_alvo_id: uuid.UUID, rotulo: str, nivel_confianca: Decimal,
        now: datetime,
    ) -> "AIClassification":
        return cls(
            id=uuid.uuid4(), tenant_id=tenant_id, inferencia_ia_id=inferencia_ia_id,
            tipo_classificacao=tipo_classificacao, entidade_alvo_tipo=entidade_alvo_tipo,
            entidade_alvo_id=entidade_alvo_id, rotulo=rotulo, nivel_confianca=nivel_confianca, criado_em=now,
        )
