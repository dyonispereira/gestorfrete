from __future__ import annotations

from enum import StrEnum


class ModelType(StrEnum):
    CLASSIFICACAO = "CLASSIFICACAO"
    PREDICAO = "PREDICAO"
    OTIMIZACAO = "OTIMIZACAO"
    VISAO_COMPUTACIONAL = "VISAO_COMPUTACIONAL"
    GERACAO_DE_TEXTO = "GERACAO_DE_TEXTO"
