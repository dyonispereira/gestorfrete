from __future__ import annotations

import uuid
from datetime import datetime

from shared_kernel.domain.base_entity import BaseEntity


class CorrectionLetter(BaseEntity[uuid.UUID]):
    """`cartas_correcao` — Carta de Correção (CC-e), sub-recurso append-only de `Cte` (D109/D282):
    nunca altera o CT-e pai, ela mesma é o histórico (D037)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        cte_id: uuid.UUID,
        numero_sequencial: int,
        texto_correcao: str,
        xml_arquivo_id: uuid.UUID | None,
        data_hora_envio: datetime,
    ) -> None:
        super().__init__(id)
        self.cte_id = cte_id
        self.numero_sequencial = numero_sequencial
        self.texto_correcao = texto_correcao
        self.xml_arquivo_id = xml_arquivo_id
        self.data_hora_envio = data_hora_envio

    @classmethod
    def create(
        cls, *, cte_id: uuid.UUID, numero_sequencial: int, texto_correcao: str, now: datetime
    ) -> "CorrectionLetter":
        return cls(
            id=uuid.uuid4(), cte_id=cte_id, numero_sequencial=numero_sequencial,
            texto_correcao=texto_correcao, xml_arquivo_id=None, data_hora_envio=now,
        )
