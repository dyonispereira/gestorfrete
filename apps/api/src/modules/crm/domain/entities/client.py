from __future__ import annotations

import uuid
from datetime import datetime

from core.exceptions.base import ConflictError
from modules.crm.domain.value_objects.client_status import ClientStatus
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class Client(BaseAggregateRoot[uuid.UUID]):
    """Aggregate Root de `crm` — `docs/domain/001-cadastros.md` "Cliente". `Contato do Cliente` é
    parte do mesmo agregado no Domain Model, mas é lido/salvo pelo seu próprio Repository (não
    carregado em memória aqui) — `CLIENT_IMPLEMENTATION.md`."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        codigo: str,
        razao_social: str,
        nome_fantasia: str | None,
        document: str,
        telefone: str | None,
        email: str | None,
        status: ClientStatus,
        audit: AuditMetadata,
    ) -> None:
        super().__init__(id)
        self.codigo = codigo
        self.razao_social = razao_social
        self.nome_fantasia = nome_fantasia
        self.document = document
        self.telefone = telefone
        self.email = email
        self.status = status
        self.audit = audit

    @classmethod
    def create(
        cls,
        *,
        codigo: str,
        razao_social: str,
        nome_fantasia: str | None,
        document: str,
        telefone: str | None,
        email: str | None,
        audit: AuditMetadata,
    ) -> "Client":
        return cls(
            id=uuid.uuid4(),
            codigo=codigo,
            razao_social=razao_social,
            nome_fantasia=nome_fantasia,
            document=document,
            telefone=telefone,
            email=email,
            status=ClientStatus.ATIVO,
            audit=audit,
        )

    def update(
        self,
        *,
        razao_social: str | None,
        nome_fantasia: str | None,
        telefone: str | None,
        email: str | None,
        updated_by: uuid.UUID,
        now: datetime,
    ) -> None:
        if razao_social is not None:
            self.razao_social = razao_social
        if nome_fantasia is not None:
            self.nome_fantasia = nome_fantasia
        if telefone is not None:
            self.telefone = telefone
        if email is not None:
            self.email = email
        self.audit = self.audit.touched(by=updated_by, at=now)

    def deactivate(self, *, deactivated_by: uuid.UUID, now: datetime) -> None:
        if self.audit.is_deleted:
            raise ConflictError("CRM_CLIENT_ALREADY_INACTIVE", "Cliente já está inativo.")
        self.status = ClientStatus.INATIVO
        self.audit = self.audit.soft_deleted(by=deactivated_by, at=now)
