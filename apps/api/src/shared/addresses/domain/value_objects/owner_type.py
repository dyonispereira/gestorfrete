from __future__ import annotations

from enum import StrEnum


class OwnerType(StrEnum):
    """Espelha `enderecos_entidade_tipo_enum` (`relational/002-cadastros.md`, D231). `FILIAL` já
    existe fisicamente mas nenhum módulo a usa ainda — `Filial`/`Branch` (`tenancy`) não foi
    implementada neste lote (`ADDRESS_IMPLEMENTATION.md`)."""

    CLIENTE = "CLIENTE"
    FORNECEDOR = "FORNECEDOR"
    FILIAL = "FILIAL"
