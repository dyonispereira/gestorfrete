from __future__ import annotations

from enum import StrEnum


class AddressType(StrEnum):
    """Espelha `enderecos_tipo_endereco_enum` (`relational/002-cadastros.md`)."""

    PRINCIPAL = "PRINCIPAL"
    COBRANCA = "COBRANCA"
    ENTREGA = "ENTREGA"
    OUTRO = "OUTRO"
