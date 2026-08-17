from __future__ import annotations

from enum import StrEnum


class ExportStatus(StrEnum):
    PROCESSANDO = "PROCESSANDO"
    CONCLUIDA = "CONCLUIDA"
    FALHOU = "FALHOU"
