from __future__ import annotations

from enum import StrEnum


class SensorType(StrEnum):
    """D120 — vocabulário extensível via `ALTER TYPE ... ADD VALUE`, nunca texto livre. Onze valores
    hoje (`relational/008-rastreamento.md`); um novo sensor é uma migration pequena e explícita."""

    IGNICAO = "IGNICAO"
    VELOCIDADE = "VELOCIDADE"
    BATERIA = "BATERIA"
    TENSAO = "TENSAO"
    ODOMETRO = "ODOMETRO"
    HORIMETRO = "HORIMETRO"
    RPM = "RPM"
    TEMPERATURA = "TEMPERATURA"
    COMBUSTIVEL = "COMBUSTIVEL"
    ACELERACAO = "ACELERACAO"
    FRENAGEM = "FRENAGEM"
