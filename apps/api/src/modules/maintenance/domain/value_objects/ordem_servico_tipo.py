from __future__ import annotations

from enum import StrEnum


class OrdemServicoTipo(StrEnum):
    PREVENTIVA = "PREVENTIVA"
    CORRETIVA = "CORRETIVA"
    EMERGENCIAL = "EMERGENCIAL"
    GARANTIA = "GARANTIA"
