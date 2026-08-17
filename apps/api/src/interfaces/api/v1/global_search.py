from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.multitenancy.context import get_current_tenant_id
from modules.crm.infrastructure.persistence.models.client_model import ClientModel
from modules.documents.infrastructure.persistence.models.cte_model import CteModel
from modules.drivers.infrastructure.persistence.models.driver_model import DriverModel
from modules.fleet.infrastructure.persistence.models.vehicle_model import VehicleModel
from modules.freight.infrastructure.persistence.models.trip_model import TripModel
from modules.identity_access.application.authorization_service import AuthorizationService
from shared_kernel.domain.actor import AuthenticatedActor

# D317 — busca nunca é uma segunda superfície de autorização: cada tipo só entra no agrupamento se o
# ator já tiver a MESMA permissão `.view` que o endpoint direto daquele tipo exige. D417 —
# `ordem_servico` (maintenance.work_order.view) fica de fora: nenhuma tabela de Ordem de Serviço
# existe no Backend ainda (só Fornecedor foi implementado em `maintenance`).
_SEARCHABLE_TYPES: dict[str, str] = {
    "viagem": "freight.trip.view",
    "cliente": "crm.client.view",
    "veiculo": "fleet.vehicle.view",
    "motorista": "drivers.driver.view",
    "cte": "documents.cte.view",
}


@dataclass(frozen=True)
class SearchResultItem:
    id: str
    label: str
    entity_type: str


@dataclass(frozen=True)
class SearchResultGroup:
    entity_type: str
    total_matches: int
    items: list[SearchResultItem]


async def run_global_search(
    *, actor: AuthenticatedActor, session_factory: async_sessionmaker[AsyncSession], q: str,
    types: list[str] | None, limit: int,
) -> list[SearchResultGroup]:
    authz = AuthorizationService(session_factory)
    granted = await authz.get_permission_codes(actor)
    enabled_types = [t for t in (types or list(_SEARCHABLE_TYPES)) if t in _SEARCHABLE_TYPES]

    tenant_id = get_current_tenant_id()
    like = f"%{q}%"
    groups: list[SearchResultGroup] = []

    async with session_factory() as session:
        for entity_type in enabled_types:
            permission_code = _SEARCHABLE_TYPES[entity_type]
            if permission_code not in granted:
                continue

            if entity_type == "viagem":
                stmt = select(TripModel.id, TripModel.codigo).where(
                    TripModel.tenant_id == tenant_id, TripModel.excluido_em.is_(None), TripModel.codigo.ilike(like)
                )
            elif entity_type == "cliente":
                stmt = select(ClientModel.id, ClientModel.razao_social).where(
                    ClientModel.tenant_id == tenant_id, ClientModel.excluido_em.is_(None),
                    ClientModel.razao_social.ilike(like) | ClientModel.cnpj_cpf.ilike(like),
                )
            elif entity_type == "veiculo":
                stmt = select(VehicleModel.id, VehicleModel.placa).where(
                    VehicleModel.tenant_id == tenant_id, VehicleModel.excluido_em.is_(None),
                    VehicleModel.placa.ilike(like),
                )
            elif entity_type == "motorista":
                stmt = select(DriverModel.id, DriverModel.nome).where(
                    DriverModel.tenant_id == tenant_id, DriverModel.excluido_em.is_(None),
                    DriverModel.nome.ilike(like) | DriverModel.cpf.ilike(like),
                )
            else:  # cte
                stmt = select(CteModel.id, CteModel.numero).where(
                    CteModel.tenant_id == tenant_id,
                    CteModel.numero.ilike(like) | CteModel.chave_acesso.ilike(like),
                )

            rows = (await session.execute(stmt.limit(limit))).all()
            if not rows:
                continue
            groups.append(
                SearchResultGroup(
                    entity_type=entity_type, total_matches=len(rows),
                    items=[SearchResultItem(id=str(row[0]), label=str(row[1]), entity_type=entity_type) for row in rows],
                )
            )

    return groups
