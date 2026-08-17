from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.maintenance.application.commands.create_supplier import CreateSupplierCommand, CreateSupplierHandler
from modules.maintenance.application.commands.deactivate_supplier import (
    DeactivateSupplierCommand,
    DeactivateSupplierHandler,
)
from modules.maintenance.application.commands.update_supplier import UpdateSupplierCommand, UpdateSupplierHandler
from modules.maintenance.application.queries.get_supplier import GetSupplierHandler, GetSupplierQuery
from modules.maintenance.application.queries.list_suppliers import ListSuppliersHandler, ListSuppliersQuery
from modules.maintenance.domain.value_objects.supplier_category import SupplierCategory
from modules.maintenance.interfaces.schemas.supplier_schemas import (
    CreateSupplierRequest,
    SupplierResponse,
    UpdateSupplierRequest,
)
from shared.addresses.application.commands.create_address import CreateAddressCommand, CreateAddressHandler
from shared.addresses.application.commands.delete_address import DeleteAddressCommand, DeleteAddressHandler
from shared.addresses.application.commands.update_address import UpdateAddressCommand, UpdateAddressHandler
from shared.addresses.application.queries.get_address import GetAddressHandler, GetAddressQuery
from shared.addresses.application.queries.list_addresses import ListAddressesHandler, ListAddressesQuery
from shared.addresses.domain.value_objects.address_type import AddressType
from shared.addresses.domain.value_objects.owner_type import OwnerType
from shared.addresses.interfaces.schemas.address_schemas import (
    AddressResponse,
    CreateAddressRequest,
    UpdateAddressRequest,
)
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.get("")
async def list_suppliers(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    category: str | None = None,
    search: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("maintenance.supplier.view")),
) -> dict[str, Any]:
    handler = ListSuppliersHandler(get_session_factory())
    result = await handler.handle(
        ListSuppliersQuery(actor=actor, page=page, limit=limit, status=status, category=category, search=search)
    )
    return {
        "data": [SupplierResponse.from_dto(s) for s in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("maintenance.supplier.view")),
) -> SupplierResponse:
    handler = GetSupplierHandler(get_session_factory())
    dto = await handler.handle(GetSupplierQuery(actor=actor, supplier_id=supplier_id))
    return SupplierResponse.from_dto(dto)


@router.post("", response_model=SupplierResponse, status_code=201)
async def create_supplier(
    body: CreateSupplierRequest,
    actor: AuthenticatedActor = Depends(require_permission("maintenance.supplier.create")),
) -> SupplierResponse:
    handler = CreateSupplierHandler()
    dto = await handler.handle(
        CreateSupplierCommand(
            actor=actor,
            razao_social=body.razao_social,
            cnpj=body.cnpj,
            telefone=body.telefone,
            category=SupplierCategory(body.category) if body.category else None,
        )
    )
    return SupplierResponse.from_dto(dto)


@router.patch("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: uuid.UUID,
    body: UpdateSupplierRequest,
    actor: AuthenticatedActor = Depends(require_permission("maintenance.supplier.edit")),
) -> SupplierResponse:
    handler = UpdateSupplierHandler()
    dto = await handler.handle(
        UpdateSupplierCommand(
            actor=actor,
            supplier_id=supplier_id,
            razao_social=body.razao_social,
            telefone=body.telefone,
            category=SupplierCategory(body.category) if body.category else None,
        )
    )
    return SupplierResponse.from_dto(dto)


@router.delete("/{supplier_id}", status_code=204, response_model=None)
async def deactivate_supplier(
    supplier_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("maintenance.supplier.delete")),
) -> None:
    handler = DeactivateSupplierHandler()
    await handler.handle(DeactivateSupplierCommand(actor=actor, supplier_id=supplier_id))


# --- Endereços (sub-recurso compartilhado, polimórfico — 011-addresses.md / D354) ---


@router.get("/{supplier_id}/addresses")
async def list_supplier_addresses(
    supplier_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("maintenance.supplier.view")),
) -> dict[str, Any]:
    await GetSupplierHandler(get_session_factory()).handle(GetSupplierQuery(actor=actor, supplier_id=supplier_id))
    handler = ListAddressesHandler(get_session_factory())
    addresses = await handler.handle(
        ListAddressesQuery(actor=actor, owner_type=OwnerType.FORNECEDOR, owner_id=supplier_id)
    )
    return {
        "data": [AddressResponse.from_dto(a) for a in addresses],
        "meta": {"pagination": {"page": 1, "limit": len(addresses) or 1, "total": len(addresses)}},
    }


@router.get("/{supplier_id}/addresses/{address_id}", response_model=AddressResponse)
async def get_supplier_address(
    supplier_id: uuid.UUID,
    address_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("maintenance.supplier.view")),
) -> AddressResponse:
    handler = GetAddressHandler(get_session_factory())
    dto = await handler.handle(
        GetAddressQuery(actor=actor, owner_type=OwnerType.FORNECEDOR, owner_id=supplier_id, address_id=address_id)
    )
    return AddressResponse.from_dto(dto)


@router.post("/{supplier_id}/addresses", response_model=AddressResponse, status_code=201)
async def create_supplier_address(
    supplier_id: uuid.UUID,
    body: CreateAddressRequest,
    actor: AuthenticatedActor = Depends(require_permission("maintenance.supplier.edit")),
) -> AddressResponse:
    await GetSupplierHandler(get_session_factory()).handle(GetSupplierQuery(actor=actor, supplier_id=supplier_id))
    handler = CreateAddressHandler()
    dto = await handler.handle(
        CreateAddressCommand(
            actor=actor,
            owner_type=OwnerType.FORNECEDOR,
            owner_id=supplier_id,
            tipo=AddressType(body.type),
            logradouro=body.logradouro,
            numero=body.numero,
            complemento=body.complemento,
            bairro=body.bairro,
            cidade=body.cidade,
            uf=body.uf,
            cep=body.cep,
        )
    )
    return AddressResponse.from_dto(dto)


@router.patch("/{supplier_id}/addresses/{address_id}", response_model=AddressResponse)
async def update_supplier_address(
    supplier_id: uuid.UUID,
    address_id: uuid.UUID,
    body: UpdateAddressRequest,
    actor: AuthenticatedActor = Depends(require_permission("maintenance.supplier.edit")),
) -> AddressResponse:
    handler = UpdateAddressHandler()
    dto = await handler.handle(
        UpdateAddressCommand(
            actor=actor,
            owner_type=OwnerType.FORNECEDOR,
            owner_id=supplier_id,
            address_id=address_id,
            tipo=AddressType(body.type) if body.type is not None else None,
            logradouro=body.logradouro,
            numero=body.numero,
            complemento=body.complemento,
            bairro=body.bairro,
            cidade=body.cidade,
            uf=body.uf,
            cep=body.cep,
        )
    )
    return AddressResponse.from_dto(dto)


@router.delete("/{supplier_id}/addresses/{address_id}", status_code=204, response_model=None)
async def delete_supplier_address(
    supplier_id: uuid.UUID,
    address_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("maintenance.supplier.edit")),
) -> None:
    handler = DeleteAddressHandler()
    await handler.handle(
        DeleteAddressCommand(actor=actor, owner_type=OwnerType.FORNECEDOR, owner_id=supplier_id, address_id=address_id)
    )
