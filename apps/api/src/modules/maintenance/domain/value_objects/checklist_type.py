from __future__ import annotations

from enum import StrEnum


class ChecklistType(StrEnum):
    MOTORISTA_SAIDA = "MOTORISTA_SAIDA"
    MOTORISTA_RETORNO = "MOTORISTA_RETORNO"
    OFICINA = "OFICINA"
    ADMINISTRATIVO = "ADMINISTRATIVO"
    CARREGAMENTO = "CARREGAMENTO"
    DESCARGA = "DESCARGA"
