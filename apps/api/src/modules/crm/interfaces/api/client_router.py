from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.crm.application.commands.create_client import CreateClientCommand, CreateClientHandler
from modules.crm.application.commands.create_client_contact import (
    CreateClientContactCommand,
    CreateClientContactHandler,
)
from modules.crm.application.commands.deactivate_client import DeactivateClientCommand, DeactivateClientHandler
from modules.crm.application.commands.delete_client_contact import (
    DeleteClientContactCommand,
    DeleteClientContactHandler,
)
from modules.crm.application.commands.update_client import UpdateClientCommand, UpdateClientHandler
from modules.crm.application.commands.update_client_contact import (
    UpdateClientContactCommand,
    UpdateClientContactHandler,
)
from modules.crm.application.queries.get_client import GetClientHandler, GetClientQuery
from modules.crm.application.queries.get_client_contact import GetClientContactHandler, GetClientContactQuery
from modules.crm.application.queries.list_client_contacts import (
    ListClientContactsHandler,
    ListClientContactsQuery,
)
from modules.crm.application.queries.list_clients import ListClientsHandler, ListClientsQuery
from modules.crm.interfaces.schemas.client_schemas import (
    ClientContactResponse,
    ClientResponse,
    CreateClientContactRequest,
    CreateClientRequest,
    UpdateClientContactRequest,
    UpdateClientRequest,
)
from modules.identity_access.interfaces.dependencies.authorization import require_permission
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

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("")
async def list_clients(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    document: str | None = None,
    search: str | None = None,
    actor: AuthenticatedActor = Depends(require_permission("crm.client.view")),
) -> dict[str, Any]:
    handler = ListClientsHandler(get_session_factory())
    result = await handler.handle(
        ListClientsQuery(actor=actor, page=page, limit=limit, status=status, document=document, search=search)
    )
    return {
        "data": [ClientResponse.from_dto(c) for c in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("crm.client.view")),
) -> ClientResponse:
    handler = GetClientHandler(get_session_factory())
    dto = await handler.handle(GetClientQuery(actor=actor, client_id=client_id))
    return ClientResponse.from_dto(dto)


@router.post("", response_model=ClientResponse, status_code=201)
async def create_client(
    body: CreateClientRequest,
    actor: AuthenticatedActor = Depends(require_permission("crm.client.create")),
) -> ClientResponse:
    handler = CreateClientHandler()
    dto = await handler.handle(
        CreateClientCommand(
            actor=actor,
            razao_social=body.razao_social,
            nome_fantasia=body.nome_fantasia,
            document=body.document,
            telefone=body.telefone,
            email=body.email,
        )
    )
    return ClientResponse.from_dto(dto)


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: uuid.UUID,
    body: UpdateClientRequest,
    actor: AuthenticatedActor = Depends(require_permission("crm.client.edit")),
) -> ClientResponse:
    handler = UpdateClientHandler()
    dto = await handler.handle(
        UpdateClientCommand(
            actor=actor,
            client_id=client_id,
            razao_social=body.razao_social,
            nome_fantasia=body.nome_fantasia,
            telefone=body.telefone,
            email=body.email,
        )
    )
    return ClientResponse.from_dto(dto)


@router.delete("/{client_id}", status_code=204, response_model=None)
async def deactivate_client(
    client_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("crm.client.delete")),
) -> None:
    handler = DeactivateClientHandler()
    await handler.handle(DeactivateClientCommand(actor=actor, client_id=client_id))


# --- Contatos (sub-recurso exclusivo de Cliente, não polimórfico — 012-contacts.md) ---


@router.get("/{client_id}/contacts")
async def list_client_contacts(
    client_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("crm.client_contact.view")),
) -> dict[str, Any]:
    handler = ListClientContactsHandler(get_session_factory())
    contacts = await handler.handle(ListClientContactsQuery(actor=actor, client_id=client_id))
    return {
        "data": [ClientContactResponse.from_dto(c) for c in contacts],
        "meta": {"pagination": {"page": 1, "limit": len(contacts) or 1, "total": len(contacts)}},
    }


@router.get("/{client_id}/contacts/{contact_id}", response_model=ClientContactResponse)
async def get_client_contact(
    client_id: uuid.UUID,
    contact_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("crm.client_contact.view")),
) -> ClientContactResponse:
    handler = GetClientContactHandler(get_session_factory())
    dto = await handler.handle(GetClientContactQuery(actor=actor, client_id=client_id, contact_id=contact_id))
    return ClientContactResponse.from_dto(dto)


@router.post("/{client_id}/contacts", response_model=ClientContactResponse, status_code=201)
async def create_client_contact(
    client_id: uuid.UUID,
    body: CreateClientContactRequest,
    actor: AuthenticatedActor = Depends(require_permission("crm.client_contact.create")),
) -> ClientContactResponse:
    handler = CreateClientContactHandler()
    dto = await handler.handle(
        CreateClientContactCommand(
            actor=actor, client_id=client_id, nome=body.nome, cargo=body.cargo, telefone=body.telefone, email=body.email
        )
    )
    return ClientContactResponse.from_dto(dto)


@router.patch("/{client_id}/contacts/{contact_id}", response_model=ClientContactResponse)
async def update_client_contact(
    client_id: uuid.UUID,
    contact_id: uuid.UUID,
    body: UpdateClientContactRequest,
    actor: AuthenticatedActor = Depends(require_permission("crm.client_contact.edit")),
) -> ClientContactResponse:
    handler = UpdateClientContactHandler()
    dto = await handler.handle(
        UpdateClientContactCommand(
            actor=actor,
            client_id=client_id,
            contact_id=contact_id,
            nome=body.nome,
            cargo=body.cargo,
            telefone=body.telefone,
            email=body.email,
        )
    )
    return ClientContactResponse.from_dto(dto)


@router.delete("/{client_id}/contacts/{contact_id}", status_code=204, response_model=None)
async def delete_client_contact(
    client_id: uuid.UUID,
    contact_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("crm.client_contact.delete")),
) -> None:
    handler = DeleteClientContactHandler()
    await handler.handle(DeleteClientContactCommand(actor=actor, client_id=client_id, contact_id=contact_id))


# --- Endereços (sub-recurso compartilhado, polimórfico — 011-addresses.md / D354) ---


@router.get("/{client_id}/addresses")
async def list_client_addresses(
    client_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("crm.client.view")),
) -> dict[str, Any]:
    await GetClientHandler(get_session_factory()).handle(GetClientQuery(actor=actor, client_id=client_id))
    handler = ListAddressesHandler(get_session_factory())
    addresses = await handler.handle(ListAddressesQuery(actor=actor, owner_type=OwnerType.CLIENTE, owner_id=client_id))
    return {
        "data": [AddressResponse.from_dto(a) for a in addresses],
        "meta": {"pagination": {"page": 1, "limit": len(addresses) or 1, "total": len(addresses)}},
    }


@router.get("/{client_id}/addresses/{address_id}", response_model=AddressResponse)
async def get_client_address(
    client_id: uuid.UUID,
    address_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("crm.client.view")),
) -> AddressResponse:
    handler = GetAddressHandler(get_session_factory())
    dto = await handler.handle(
        GetAddressQuery(actor=actor, owner_type=OwnerType.CLIENTE, owner_id=client_id, address_id=address_id)
    )
    return AddressResponse.from_dto(dto)


@router.post("/{client_id}/addresses", response_model=AddressResponse, status_code=201)
async def create_client_address(
    client_id: uuid.UUID,
    body: CreateAddressRequest,
    actor: AuthenticatedActor = Depends(require_permission("crm.client.edit")),
) -> AddressResponse:
    await GetClientHandler(get_session_factory()).handle(GetClientQuery(actor=actor, client_id=client_id))
    handler = CreateAddressHandler()
    dto = await handler.handle(
        CreateAddressCommand(
            actor=actor,
            owner_type=OwnerType.CLIENTE,
            owner_id=client_id,
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


@router.patch("/{client_id}/addresses/{address_id}", response_model=AddressResponse)
async def update_client_address(
    client_id: uuid.UUID,
    address_id: uuid.UUID,
    body: UpdateAddressRequest,
    actor: AuthenticatedActor = Depends(require_permission("crm.client.edit")),
) -> AddressResponse:
    handler = UpdateAddressHandler()
    dto = await handler.handle(
        UpdateAddressCommand(
            actor=actor,
            owner_type=OwnerType.CLIENTE,
            owner_id=client_id,
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


@router.delete("/{client_id}/addresses/{address_id}", status_code=204, response_model=None)
async def delete_client_address(
    client_id: uuid.UUID,
    address_id: uuid.UUID,
    actor: AuthenticatedActor = Depends(require_permission("crm.client.edit")),
) -> None:
    handler = DeleteAddressHandler()
    await handler.handle(
        DeleteAddressCommand(actor=actor, owner_type=OwnerType.CLIENTE, owner_id=client_id, address_id=address_id)
    )
