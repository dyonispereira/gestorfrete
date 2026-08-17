from __future__ import annotations

from enum import StrEnum


class SyncItemStatus(StrEnum):
    PENDENTE = "PENDENTE"
    ENVIANDO = "ENVIANDO"
    PROCESSADA = "PROCESSADA"
    FALHOU = "FALHOU"
    CONFLITO = "CONFLITO"
