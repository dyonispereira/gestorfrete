from __future__ import annotations

from enum import StrEnum


class IntegrationConfigStatus(StrEnum):
    ATIVA = "ATIVA"
    INATIVA = "INATIVA"
    COM_ERRO = "COM_ERRO"
