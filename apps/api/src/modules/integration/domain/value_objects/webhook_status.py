from __future__ import annotations

from enum import StrEnum


class WebhookStatus(StrEnum):
    ATIVO = "ATIVO"
    INATIVO = "INATIVO"
    SUSPENSO = "SUSPENSO"
