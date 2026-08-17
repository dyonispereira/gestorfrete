from __future__ import annotations

import uuid
from datetime import datetime

from core.exceptions.base import ConflictError
from modules.maintenance.domain.value_objects.supplier_category import SupplierCategory
from modules.maintenance.domain.value_objects.supplier_status import SupplierStatus
from shared_kernel.domain.audit_metadata import AuditMetadata
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot


class Supplier(BaseAggregateRoot[uuid.UUID]):
    """Aggregate Root de `maintenance` — `docs/domain/001-cadastros.md` "Fornecedor"."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        codigo: str,
        razao_social: str,
        cnpj: str,
        telefone: str | None,
        category: SupplierCategory | None,
        status: SupplierStatus,
        audit: AuditMetadata,
    ) -> None:
        super().__init__(id)
        self.codigo = codigo
        self.razao_social = razao_social
        self.cnpj = cnpj
        self.telefone = telefone
        self.category = category
        self.status = status
        self.audit = audit

    @classmethod
    def create(
        cls,
        *,
        codigo: str,
        razao_social: str,
        cnpj: str,
        telefone: str | None,
        category: SupplierCategory | None,
        audit: AuditMetadata,
    ) -> "Supplier":
        return cls(
            id=uuid.uuid4(),
            codigo=codigo,
            razao_social=razao_social,
            cnpj=cnpj,
            telefone=telefone,
            category=category,
            status=SupplierStatus.ATIVO,
            audit=audit,
        )

    def update(
        self,
        *,
        razao_social: str | None,
        telefone: str | None,
        category: SupplierCategory | None,
        updated_by: uuid.UUID,
        now: datetime,
    ) -> None:
        if razao_social is not None:
            self.razao_social = razao_social
        if telefone is not None:
            self.telefone = telefone
        if category is not None:
            self.category = category
        self.audit = self.audit.touched(by=updated_by, at=now)

    def deactivate(self, *, deactivated_by: uuid.UUID, now: datetime) -> None:
        if self.audit.is_deleted:
            raise ConflictError("MAINTENANCE_SUPPLIER_ALREADY_INACTIVE", "Fornecedor já está inativo.")
        self.status = SupplierStatus.INATIVO
        self.audit = self.audit.soft_deleted(by=deactivated_by, at=now)
