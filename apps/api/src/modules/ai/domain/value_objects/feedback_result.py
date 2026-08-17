from __future__ import annotations

from enum import StrEnum


class FeedbackResult(StrEnum):
    ACEITO = "ACEITO"
    REJEITADO = "REJEITADO"
    IGNORADO = "IGNORADO"
