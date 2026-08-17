from __future__ import annotations

from enum import StrEnum


class VehicleDocumentStatus(StrEnum):
    """Calculado na leitura a partir de `data_validade` — mesmo padrão de `DriverDocument.status`
    (Lote 3), nunca uma coluna gravada como fonte de verdade separada."""

    VALIDO = "VALIDO"
    VENCIDO = "VENCIDO"
