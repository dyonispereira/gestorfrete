from __future__ import annotations

import uuid
from datetime import datetime

from modules.ai.domain.value_objects.feedback_output_type import FeedbackOutputType
from modules.ai.domain.value_objects.feedback_result import FeedbackResult
from shared_kernel.domain.base_entity import BaseEntity


class AIFeedback(BaseEntity[uuid.UUID]):
    """`feedbacks_ia` (D165) — matéria-prima para evolução futura dos modelos; nunca altera a
    decisão original do usuário nem a saída de IA avaliada. `resultado`/`justificativa` são a
    decisão pontual do momento, imutável; `resultado_real` (D192) é observação tardia, o único campo
    editável via `PATCH`."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        tenant_id: uuid.UUID,
        saida_ia_tipo: FeedbackOutputType,
        saida_ia_id: uuid.UUID,
        usuario_id: uuid.UUID,
        resultado: FeedbackResult,
        justificativa: str | None,
        resultado_real: str | None,
        criado_em: datetime,
    ) -> None:
        super().__init__(id)
        self.tenant_id = tenant_id
        self.saida_ia_tipo = saida_ia_tipo
        self.saida_ia_id = saida_ia_id
        self.usuario_id = usuario_id
        self.resultado = resultado
        self.justificativa = justificativa
        self.resultado_real = resultado_real
        self.criado_em = criado_em

    @classmethod
    def create(
        cls, *, tenant_id: uuid.UUID, saida_ia_tipo: FeedbackOutputType, saida_ia_id: uuid.UUID,
        usuario_id: uuid.UUID, resultado: FeedbackResult, justificativa: str | None,
        resultado_real: str | None, now: datetime,
    ) -> "AIFeedback":
        return cls(
            id=uuid.uuid4(), tenant_id=tenant_id, saida_ia_tipo=saida_ia_tipo, saida_ia_id=saida_ia_id,
            usuario_id=usuario_id, resultado=resultado, justificativa=justificativa,
            resultado_real=resultado_real, criado_em=now,
        )

    def record_actual_result(self, *, resultado_real: str) -> None:
        """`077` — único campo editável via `PATCH`; `resultado`/`justificativa` permanecem
        imutáveis (D165 — Feedback nunca reabre a decisão original)."""

        self.resultado_real = resultado_real
