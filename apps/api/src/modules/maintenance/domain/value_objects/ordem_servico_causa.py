from __future__ import annotations

from enum import StrEnum


class OrdemServicoCausa(StrEnum):
    DESGASTE = "DESGASTE"
    QUEBRA = "QUEBRA"
    ACIDENTE = "ACIDENTE"
    MAU_USO = "MAU_USO"
    INSPECAO = "INSPECAO"
    RECALL = "RECALL"
