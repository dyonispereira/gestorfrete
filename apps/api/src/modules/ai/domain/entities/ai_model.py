from __future__ import annotations

import uuid

from modules.ai.domain.value_objects.logical_provider import LogicalProvider
from modules.ai.domain.value_objects.model_status import ModelStatus
from modules.ai.domain.value_objects.model_type import ModelType
from shared_kernel.domain.base_entity import BaseEntity


class AIModel(BaseEntity[uuid.UUID]):
    """`modelos_ia` (D169/D170) — Reference Data. Múltiplos modelos `ATIVO` simultâneos é o
    esperado. `fornecedor_logico` nunca é o nome de um provedor real (D170/D309) — apenas a
    identidade lógica deste registro. Nova versão nasce como uma linha física nova (`uq_modelos_ia_
    nome_versao`), nunca uma transformação desta entidade."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        tenant_id: uuid.UUID | None,
        nome: str,
        tipo: ModelType,
        versao: str,
        fornecedor_logico: LogicalProvider,
        capacidade: str,
        contexto_maximo: int | None,
        status: ModelStatus,
    ) -> None:
        super().__init__(id)
        self.tenant_id = tenant_id
        self.nome = nome
        self.tipo = tipo
        self.versao = versao
        self.fornecedor_logico = fornecedor_logico
        self.capacidade = capacidade
        self.contexto_maximo = contexto_maximo
        self.status = status

    @classmethod
    def create(
        cls, *, tenant_id: uuid.UUID | None, nome: str, tipo: ModelType, versao: str,
        fornecedor_logico: LogicalProvider, capacidade: str, contexto_maximo: int | None,
    ) -> "AIModel":
        return cls(
            id=uuid.uuid4(), tenant_id=tenant_id, nome=nome, tipo=tipo, versao=versao,
            fornecedor_logico=fornecedor_logico, capacidade=capacidade, contexto_maximo=contexto_maximo,
            status=ModelStatus.EM_TREINAMENTO,
        )

    def update_fields(
        self, *, capacidade: str | None, contexto_maximo: int | None, status: ModelStatus | None,
    ) -> None:
        """`071` — D229 parcial: só `capability`/`max_context`/`status`. `name`/`type`/`version`/
        `logical_provider` nunca editáveis (identidade do modelo)."""

        if capacidade is not None:
            self.capacidade = capacidade
        if contexto_maximo is not None:
            self.contexto_maximo = contexto_maximo
        if status is not None:
            self.status = status
