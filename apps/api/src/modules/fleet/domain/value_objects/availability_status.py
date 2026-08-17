from __future__ import annotations

from enum import StrEnum


class AvailabilityStatus(StrEnum):
    DISPONIVEL = "DISPONIVEL"
    EM_VIAGEM = "EM_VIAGEM"
    EM_MANUTENCAO = "EM_MANUTENCAO"
    INATIVO = "INATIVO"
