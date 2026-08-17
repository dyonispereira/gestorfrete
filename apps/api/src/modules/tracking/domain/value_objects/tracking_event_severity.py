from __future__ import annotations

from enum import StrEnum


class TrackingEventSeverity(StrEnum):
    """D127 — todo Evento de Rastreamento tem severidade, independente do `tipo`."""

    INFORMACAO = "INFORMACAO"
    ATENCAO = "ATENCAO"
    ALERTA = "ALERTA"
    CRITICO = "CRITICO"
