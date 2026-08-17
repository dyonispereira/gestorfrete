from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from core.exceptions.base import ConflictError
from modules.ai.domain.value_objects.suggestion_status import SuggestionStatus
from shared_kernel.domain.base_entity import BaseEntity


class AISuggestion(BaseEntity[uuid.UUID]):
    """`sugestoes_ia` (D310/D311) — produto derivado da Inferência, nunca fundido com ela. D161: a
    decisão do usuário (`accept`/`reject`/`ignore`) nunca executa o comando operacional
    correspondente por conta própria — só registra a decisão."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        tenant_id: uuid.UUID,
        inferencia_ia_id: uuid.UUID,
        categoria: str,
        entidade_alvo_tipo: str,
        entidade_alvo_id: uuid.UUID,
        recomendacao: str,
        justificativa: str,
        nivel_confianca: Decimal,
        status: SuggestionStatus,
        usuario_decisao_id: uuid.UUID | None,
        data_hora_decisao: datetime | None,
    ) -> None:
        super().__init__(id)
        self.tenant_id = tenant_id
        self.inferencia_ia_id = inferencia_ia_id
        self.categoria = categoria
        self.entidade_alvo_tipo = entidade_alvo_tipo
        self.entidade_alvo_id = entidade_alvo_id
        self.recomendacao = recomendacao
        self.justificativa = justificativa
        self.nivel_confianca = nivel_confianca
        self.status = status
        self.usuario_decisao_id = usuario_decisao_id
        self.data_hora_decisao = data_hora_decisao

    @classmethod
    def create(
        cls, *, tenant_id: uuid.UUID, inferencia_ia_id: uuid.UUID, categoria: str,
        entidade_alvo_tipo: str, entidade_alvo_id: uuid.UUID, recomendacao: str, justificativa: str,
        nivel_confianca: Decimal,
    ) -> "AISuggestion":
        return cls(
            id=uuid.uuid4(), tenant_id=tenant_id, inferencia_ia_id=inferencia_ia_id, categoria=categoria,
            entidade_alvo_tipo=entidade_alvo_tipo, entidade_alvo_id=entidade_alvo_id,
            recomendacao=recomendacao, justificativa=justificativa, nivel_confianca=nivel_confianca,
            status=SuggestionStatus.PENDENTE, usuario_decisao_id=None, data_hora_decisao=None,
        )

    def _decide(self, *, status: SuggestionStatus, usuario_id: uuid.UUID, now: datetime) -> None:
        if self.status != SuggestionStatus.PENDENTE:
            raise ConflictError(
                "AI_SUGGESTION_INVALID_TRANSITION", "Sugestão já foi decidida ou expirou."
            )
        self.status = status
        self.usuario_decisao_id = usuario_id
        self.data_hora_decisao = now

    def accept(self, *, usuario_id: uuid.UUID, now: datetime) -> None:
        """D311 — só registra a decisão; executar a ação sugerida é sempre uma chamada separada e
        explícita ao comando do bounded context operacional responsável, nunca feita aqui."""

        self._decide(status=SuggestionStatus.ACEITA, usuario_id=usuario_id, now=now)

    def reject(self, *, usuario_id: uuid.UUID, now: datetime) -> None:
        self._decide(status=SuggestionStatus.REJEITADA, usuario_id=usuario_id, now=now)

    def ignore(self, *, usuario_id: uuid.UUID, now: datetime) -> None:
        self._decide(status=SuggestionStatus.IGNORADA, usuario_id=usuario_id, now=now)
