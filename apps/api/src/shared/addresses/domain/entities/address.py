from __future__ import annotations

import uuid
from datetime import datetime

from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot
from shared.addresses.domain.value_objects.address_type import AddressType
from shared.addresses.domain.value_objects.owner_type import OwnerType


class Address(BaseAggregateRoot[uuid.UUID]):
    """Implementação física de `Endereço` (D182/D354) — `docs/domain/001-cadastros.md`. Não é um
    Aggregate Root no Domain Model de negócio (é parte do agregado da entidade-dona), mas é seu
    próprio Aggregate Root técnico aqui: `crm`/`maintenance` nunca carregam `Address` dentro do
    objeto Python `Client`/`Supplier` — cada endereço é lido/salvo pelo seu próprio Repository
    (`ADDRESS_IMPLEMENTATION.md`)."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        owner_type: OwnerType,
        owner_id: uuid.UUID,
        tipo: AddressType,
        logradouro: str,
        numero: str | None,
        complemento: str | None,
        bairro: str,
        cidade: str,
        uf: str,
        cep: str,
        audit: AuditMetadata,
    ) -> None:
        super().__init__(id)
        self.owner_type = owner_type
        self.owner_id = owner_id
        self.tipo = tipo
        self.logradouro = logradouro
        self.numero = numero
        self.complemento = complemento
        self.bairro = bairro
        self.cidade = cidade
        self.uf = uf
        self.cep = cep
        self.audit = audit

    @classmethod
    def create(
        cls,
        *,
        owner_type: OwnerType,
        owner_id: uuid.UUID,
        tipo: AddressType,
        logradouro: str,
        numero: str | None,
        complemento: str | None,
        bairro: str,
        cidade: str,
        uf: str,
        cep: str,
        audit: AuditMetadata,
    ) -> "Address":
        return cls(
            id=uuid.uuid4(),
            owner_type=owner_type,
            owner_id=owner_id,
            tipo=tipo,
            logradouro=logradouro,
            numero=numero,
            complemento=complemento,
            bairro=bairro,
            cidade=cidade,
            uf=uf,
            cep=cep,
            audit=audit,
        )

    def update(
        self,
        *,
        tipo: AddressType | None,
        logradouro: str | None,
        numero: str | None,
        complemento: str | None,
        bairro: str | None,
        cidade: str | None,
        uf: str | None,
        cep: str | None,
        updated_by: uuid.UUID,
        now: datetime,
    ) -> None:
        if tipo is not None:
            self.tipo = tipo
        if logradouro is not None:
            self.logradouro = logradouro
        if numero is not None:
            self.numero = numero
        if complemento is not None:
            self.complemento = complemento
        if bairro is not None:
            self.bairro = bairro
        if cidade is not None:
            self.cidade = cidade
        if uf is not None:
            self.uf = uf
        if cep is not None:
            self.cep = cep
        self.audit = self.audit.touched(by=updated_by, at=now)

    def soft_delete(self, *, deleted_by: uuid.UUID, now: datetime) -> None:
        self.audit = self.audit.soft_deleted(by=deleted_by, at=now)
