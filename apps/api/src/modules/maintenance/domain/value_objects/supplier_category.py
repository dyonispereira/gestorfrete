from __future__ import annotations

from enum import StrEnum


class SupplierCategory(StrEnum):
    """Espelha `fornecedores_tipo_principal_enum` (`relational/002-cadastros.md`) — um único
    recurso `Supplier` cobre todas as categorias (D076, `008-suppliers.md`)."""

    PECA = "PECA"
    RECAPAGEM = "RECAPAGEM"
    SEGURO = "SEGURO"
    OFICINA = "OFICINA"
    POSTO = "POSTO"
    BORRACHARIA = "BORRACHARIA"
    GUINCHO = "GUINCHO"
    OUTRO = "OUTRO"
