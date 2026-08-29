from __future__ import annotations

from enum import StrEnum


class ItemOrdemServicoCategoriaCusto(StrEnum):
    PECAS = "PECAS"
    PNEUS = "PNEUS"
    SERVICOS = "SERVICOS"
    TERCEIROS = "TERCEIROS"
    MAO_DE_OBRA_INTERNA = "MAO_DE_OBRA_INTERNA"
    MAO_DE_OBRA_TERCEIRIZADA = "MAO_DE_OBRA_TERCEIRIZADA"
    DESLOCAMENTO = "DESLOCAMENTO"
    OUTROS = "OUTROS"
