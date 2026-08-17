from __future__ import annotations

from enum import StrEnum


class MetricDimensionalGranularity(StrEnum):
    VIAGEM = "VIAGEM"
    VEICULO = "VEICULO"
    MOTORISTA = "MOTORISTA"
    CLIENTE = "CLIENTE"
    TENANT = "TENANT"
