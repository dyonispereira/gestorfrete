from __future__ import annotations

from enum import StrEnum


class SuggestionStatus(StrEnum):
    PENDENTE = "PENDENTE"
    ACEITA = "ACEITA"
    REJEITADA = "REJEITADA"
    IGNORADA = "IGNORADA"
    EXPIRADA = "EXPIRADA"
