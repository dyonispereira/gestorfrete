from __future__ import annotations

from enum import StrEnum


class ChecklistStatus(StrEnum):
    PENDENTE = "PENDENTE"
    EM_PREENCHIMENTO = "EM_PREENCHIMENTO"
    CONCLUIDO = "CONCLUIDO"
    APROVADO = "APROVADO"
    REPROVADO = "REPROVADO"
