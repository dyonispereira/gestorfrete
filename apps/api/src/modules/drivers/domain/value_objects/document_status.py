from __future__ import annotations

from enum import StrEnum


class DocumentStatus(StrEnum):
    """Calculado na leitura a partir de `data_validade` — nunca uma coluna gravada como fonte de
    verdade separada (`DRIVER_IMPLEMENTATION.md`)."""

    VALIDO = "VALIDO"
    VENCIDO = "VENCIDO"
