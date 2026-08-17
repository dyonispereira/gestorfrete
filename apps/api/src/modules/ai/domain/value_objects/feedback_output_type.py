from __future__ import annotations

from enum import StrEnum


class FeedbackOutputType(StrEnum):
    SUGESTAO = "SUGESTAO"
    PREDICAO = "PREDICAO"
    CLASSIFICACAO = "CLASSIFICACAO"
    ANOMALIA = "ANOMALIA"
    LEITURA_VISAO_COMPUTACIONAL = "LEITURA_VISAO_COMPUTACIONAL"
