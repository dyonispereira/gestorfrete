from __future__ import annotations

import re
import uuid

from core.exceptions.base import ValidationError
from shared_kernel.domain.base_entity import BaseEntity

_CHAVE_ACESSO_PATTERN = re.compile(r"^[0-9]{44}$")


class ReferencedNfe(BaseEntity[uuid.UUID]):
    """`nfe_referenciadas` — NF-e Referenciada, sub-recurso de `Cte`. Referência fiscal, nunca uma
    NF-e emitida pela transportadora."""

    def __init__(self, id: uuid.UUID, *, cte_id: uuid.UUID, chave_acesso: str, xml_arquivo_id: uuid.UUID | None) -> None:
        super().__init__(id)
        self.cte_id = cte_id
        self.chave_acesso = chave_acesso
        self.xml_arquivo_id = xml_arquivo_id

    @staticmethod
    def check_access_key(chave_acesso: str) -> None:
        if not _CHAVE_ACESSO_PATTERN.match(chave_acesso):
            raise ValidationError(
                "FISCAL_NFE_REFERENCE_INVALID_ACCESS_KEY", "access_key deve ter exatamente 44 dígitos."
            )

    @classmethod
    def create(cls, *, cte_id: uuid.UUID, chave_acesso: str) -> "ReferencedNfe":
        cls.check_access_key(chave_acesso)
        return cls(id=uuid.uuid4(), cte_id=cte_id, chave_acesso=chave_acesso, xml_arquivo_id=None)
