from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from core.exceptions.base import ConflictError
from modules.ai.domain.value_objects.computer_vision_reading_status import ComputerVisionReadingStatus
from modules.ai.domain.value_objects.reading_type import ReadingType
from shared_kernel.domain.base_entity import BaseEntity


class ComputerVisionReading(BaseEntity[uuid.UUID]):
    """`leituras_visao_computacional` (D161/D164) — resultado é sempre proposta, nunca aplicado
    automaticamente. `ck_leituras_visao_computacional_confirmacao_humana` (DDL): todo estado
    terminal que exigia revisão humana precisa de `usuario_confirmacao_id` — reforçado aqui
    (`confirm`/`reject`) e pela constraint física do Postgres (segunda camada, D201/D202-style)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        tenant_id: uuid.UUID,
        inferencia_ia_id: uuid.UUID,
        arquivo_origem_id: uuid.UUID,
        tipo_leitura: ReadingType,
        regiao_analisada: dict[str, Any] | None,
        resultado_extraido: dict[str, Any],
        nivel_confianca: Decimal,
        revisao_humana_necessaria: bool,
        status: ComputerVisionReadingStatus,
        usuario_confirmacao_id: uuid.UUID | None,
    ) -> None:
        super().__init__(id)
        self.tenant_id = tenant_id
        self.inferencia_ia_id = inferencia_ia_id
        self.arquivo_origem_id = arquivo_origem_id
        self.tipo_leitura = tipo_leitura
        self.regiao_analisada = regiao_analisada
        self.resultado_extraido = resultado_extraido
        self.nivel_confianca = nivel_confianca
        self.revisao_humana_necessaria = revisao_humana_necessaria
        self.status = status
        self.usuario_confirmacao_id = usuario_confirmacao_id

    @classmethod
    def create(
        cls, *, tenant_id: uuid.UUID, inferencia_ia_id: uuid.UUID, arquivo_origem_id: uuid.UUID,
        tipo_leitura: ReadingType, regiao_analisada: dict[str, Any] | None,
        resultado_extraido: dict[str, Any], nivel_confianca: Decimal, revisao_humana_necessaria: bool,
    ) -> "ComputerVisionReading":
        return cls(
            id=uuid.uuid4(), tenant_id=tenant_id, inferencia_ia_id=inferencia_ia_id,
            arquivo_origem_id=arquivo_origem_id, tipo_leitura=tipo_leitura,
            regiao_analisada=regiao_analisada, resultado_extraido=resultado_extraido,
            nivel_confianca=nivel_confianca, revisao_humana_necessaria=revisao_humana_necessaria,
            status=ComputerVisionReadingStatus.PROCESSADA, usuario_confirmacao_id=None,
        )

    def _require_pending_human_review(self) -> None:
        if not self.revisao_humana_necessaria or self.status != ComputerVisionReadingStatus.PROCESSADA:
            raise ConflictError(
                "AI_CV_READING_INVALID_TRANSITION",
                "Leitura não exige revisão humana ou já foi revisada.",
            )

    def confirm(self, *, usuario_id: uuid.UUID) -> None:
        self._require_pending_human_review()
        self.status = ComputerVisionReadingStatus.CONFIRMADA
        self.usuario_confirmacao_id = usuario_id

    def reject(self, *, usuario_id: uuid.UUID) -> None:
        self._require_pending_human_review()
        self.status = ComputerVisionReadingStatus.REJEITADA
        self.usuario_confirmacao_id = usuario_id
