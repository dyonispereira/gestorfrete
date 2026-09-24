from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select, update

from core.database.session import get_session_factory
from core.multitenancy.context import reset_current_tenant_id, set_current_tenant_id
from modules.crm.infrastructure.persistence.models.client_model import ClientModel
from modules.drivers.infrastructure.persistence.models.driver_model import DriverModel
from modules.financial.infrastructure.persistence.models.accounts_payable_model import (
    AccountsPayableModel,
    ExpenseAllocationModel,
    ExpenseApprovalModel,
    PayableStatusHistoryModel,
)
from modules.financial.infrastructure.persistence.models.chart_of_accounts_model import ChartOfAccountsModel
from modules.financial.infrastructure.persistence.models.cost_center_model import CostCenterModel
from modules.fleet.infrastructure.persistence.models.vehicle_availability_model import VehicleAvailabilityModel
from modules.fleet.infrastructure.persistence.models.vehicle_category_model import VehicleCategoryModel
from modules.fleet.infrastructure.persistence.models.vehicle_impediment_model import VehicleImpedimentModel
from modules.fleet.infrastructure.persistence.models.vehicle_model import VehicleModel
from modules.freight.infrastructure.persistence.models.trip_model import TripModel
from modules.identity_access.application.commands.create_role import CreateRoleCommand, CreateRoleHandler
from modules.identity_access.application.commands.create_user import CreateUserCommand, CreateUserHandler
from modules.identity_access.infrastructure.persistence.models.identity_models import (
    PermissionModel,
    RoleModel,
    SessionModel,
    UserModel,
    papel_permissao,
    usuarios_papeis,
)
from modules.maintenance.infrastructure.persistence.models.ordem_servico_model import (
    OrdemServicoModel,
    OrdemServicoStatusHistoryModel,
)
from modules.maintenance.infrastructure.persistence.models.supplier_model import SupplierModel
from modules.tenancy.infrastructure.persistence.models.tenant_model import TenantModel
from shared_kernel.domain.actor import AuthenticatedActor

pytestmark = pytest.mark.integration
"""Lote 4 — Resultado Gerencial. Prova matematicamente as 4 dimensões (Viagem/Veículo/Cliente/
Motorista) a partir de um cenário controlado: 2 Clientes, 2 Veículos, 2 Motoristas, 5 Viagens (3
"boas", 1 CANCELADA, 1 fora do período consultado), 1 Ordem de Serviço ativa + 1 cancelada, e Contas
a Pagar cobrindo Manutenção (via OS), Outros Custos (tagueado no Veículo) e um lançamento vinculado
só ao Motorista — provando em cada dimensão que agregar nunca cria nem apaga dinheiro (D008/D090).

Este teste manipula `viagens.receita_realizada`/`custo_realizado`/`motorista_id`/
`veiculo_tracionador_id` diretamente via SQL em vez de percorrer o fluxo real Viagem→CT-e→SEFAZ→
Fatura→CR (já exaustivamente provado nos testes de `test_fiscal_flow.py`/`test_financeiro_flow.py`)
— o que está sob teste aqui é a camada de agregação/leitura nova (`ManagementResultReadRepository` e
os Query Handlers de `modules.analytics`), não o pipeline financeiro que já a alimenta. Nenhuma
Conta a Pagar `origem=VIAGEM` é criada neste arquivo — evita disparar `TripInternalTransitions.
update_realized_cost` (D390) e sobrescrever os valores fixados via SQL."""

PASSWORD = "Senha-Forte-123"

PERMISSION_CATALOG = [
    ("crm.client.create", "Criar clientes", "crm"),
    ("drivers.driver.create", "Criar motoristas", "drivers"),
    ("fleet.vehicle.create", "Criar veículos", "fleet"),
    ("freight.trip.create", "Criar viagens", "freight"),
    ("maintenance.supplier.create", "Criar fornecedores", "maintenance"),
    ("maintenance.work_order.create", "Criar ordens de serviço", "maintenance"),
    ("maintenance.work_order.cancel", "Cancelar ordens de serviço", "maintenance"),
    ("financial.cost_center.create", "Criar centros de custo", "financial"),
    ("financial.chart_of_accounts.create", "Criar plano de contas", "financial"),
    ("financial.payable.create", "Criar contas a pagar", "financial"),
    ("financial.payable.reject", "Rejeitar contas a pagar", "financial"),
    ("analytics.executive_dashboard.view", "Visualizar dashboard executivo", "analytics"),
    ("analytics.freight_report.view", "Visualizar relatório de fretes", "analytics"),
    ("analytics.maintenance_report.view", "Visualizar relatório de manutenção", "analytics"),
    ("analytics.financial_report.view", "Visualizar relatório financeiro", "analytics"),
    ("analytics.driver_report.view", "Visualizar relatório de motoristas", "analytics"),
]
ALL_PERMISSION_CODES = [c for c, _, _ in PERMISSION_CATALOG]


async def _seed_permissions() -> None:
    session_factory = get_session_factory()
    now = datetime.now(timezone.utc)
    async with session_factory() as session:
        for codigo, nome, modulo in PERMISSION_CATALOG:
            existing = (
                await session.execute(select(PermissionModel).where(PermissionModel.codigo == codigo))
            ).scalar_one_or_none()
            if existing is None:
                session.add(PermissionModel(id=uuid.uuid4(), codigo=codigo, nome=nome, modulo=modulo, criado_em=now))
        await session.commit()


async def _create_tenant() -> uuid.UUID:
    session_factory = get_session_factory()
    now = datetime.now(timezone.utc)
    tenant_id = uuid.uuid4()
    async with session_factory() as session:
        session.add(
            TenantModel(
                id=tenant_id, codigo=f"T-{tenant_id.hex[:8]}", versao=1, razao_social="Transportadora Resultado LTDA",
                cnpj=f"{tenant_id.int % 10**14:014d}", status="ATIVO", criado_em=now, atualizado_em=now,
            )
        )
        await session.commit()
    return tenant_id


async def _seed_vehicle_category(tenant_id: uuid.UUID) -> uuid.UUID:
    session_factory = get_session_factory()
    now = datetime.now(timezone.utc)
    category_id = uuid.uuid4()
    async with session_factory() as session:
        session.add(
            VehicleCategoryModel(
                id=category_id, tenant_id=tenant_id, codigo=f"CAT-{category_id.hex[:8]}",
                nome=f"Categoria {category_id.hex[:6]}", status="ATIVA", criado_em=now, atualizado_em=now,
            )
        )
        await session.commit()
    return category_id


async def _create_role(tenant_id: uuid.UUID, permission_codes: list[str]) -> uuid.UUID:
    bootstrap_actor = AuthenticatedActor(user_id=uuid.uuid4(), tenant_id=tenant_id, session_id=uuid.uuid4())
    token = set_current_tenant_id(tenant_id)
    try:
        dto = await CreateRoleHandler().handle(
            CreateRoleCommand(
                actor=bootstrap_actor, nome=f"Papel-{uuid.uuid4().hex[:8]}", descricao=None,
                permission_codes=permission_codes,
            )
        )
        return dto.id
    finally:
        reset_current_tenant_id(token)


async def _create_user(tenant_id: uuid.UUID, *, role_ids: frozenset[uuid.UUID]) -> tuple[uuid.UUID, str]:
    email = f"user-{uuid.uuid4().hex[:10]}@teste.com"
    bootstrap_actor = AuthenticatedActor(user_id=uuid.uuid4(), tenant_id=tenant_id, session_id=uuid.uuid4())
    token = set_current_tenant_id(tenant_id)
    try:
        dto = await CreateUserHandler().handle(
            CreateUserCommand(
                actor=bootstrap_actor, nome="Usuário de Teste", email=email, password=PASSWORD, driver_id=None,
                employee_id=None, role_ids=role_ids,
            )
        )
        return dto.id, email
    finally:
        reset_current_tenant_id(token)


async def _login(client: AsyncClient, email: str) -> dict[str, str]:
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _cleanup_tenant(tenant_id: uuid.UUID) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        await session.execute(delete(ExpenseAllocationModel).where(ExpenseAllocationModel.tenant_id == tenant_id))
        await session.execute(delete(ExpenseApprovalModel).where(ExpenseApprovalModel.tenant_id == tenant_id))
        await session.execute(delete(PayableStatusHistoryModel).where(PayableStatusHistoryModel.tenant_id == tenant_id))
        await session.execute(delete(AccountsPayableModel).where(AccountsPayableModel.tenant_id == tenant_id))
        await session.execute(
            delete(OrdemServicoStatusHistoryModel).where(OrdemServicoStatusHistoryModel.tenant_id == tenant_id)
        )
        await session.execute(delete(OrdemServicoModel).where(OrdemServicoModel.tenant_id == tenant_id))
        await session.execute(delete(TripModel).where(TripModel.tenant_id == tenant_id))
        await session.execute(delete(SupplierModel).where(SupplierModel.tenant_id == tenant_id))
        await session.execute(delete(CostCenterModel).where(CostCenterModel.tenant_id == tenant_id))
        await session.execute(delete(ChartOfAccountsModel).where(ChartOfAccountsModel.tenant_id == tenant_id))
        await session.execute(delete(VehicleAvailabilityModel).where(VehicleAvailabilityModel.tenant_id == tenant_id))
        await session.execute(delete(VehicleImpedimentModel).where(VehicleImpedimentModel.tenant_id == tenant_id))
        await session.execute(delete(VehicleModel).where(VehicleModel.tenant_id == tenant_id))
        await session.execute(delete(VehicleCategoryModel).where(VehicleCategoryModel.tenant_id == tenant_id))
        await session.execute(delete(DriverModel).where(DriverModel.tenant_id == tenant_id))
        await session.execute(delete(ClientModel).where(ClientModel.tenant_id == tenant_id))
        await session.execute(usuarios_papeis.delete().where(usuarios_papeis.c.usuario_id.in_(
            select(UserModel.id).where(UserModel.tenant_id == tenant_id)
        )))
        await session.execute(papel_permissao.delete().where(papel_permissao.c.papel_id.in_(
            select(RoleModel.id).where(RoleModel.tenant_id == tenant_id)
        )))
        await session.execute(delete(SessionModel).where(SessionModel.tenant_id == tenant_id))
        await session.execute(delete(UserModel).where(UserModel.tenant_id == tenant_id))
        await session.execute(delete(RoleModel).where(RoleModel.tenant_id == tenant_id))
        await session.execute(delete(TenantModel).where(TenantModel.id == tenant_id))
        await session.commit()


@pytest.fixture
async def tenants() -> AsyncIterator[list[uuid.UUID]]:
    created: list[uuid.UUID] = []
    yield created
    for tenant_id in created:
        await _cleanup_tenant(tenant_id)


@pytest.fixture(autouse=True)
async def _fresh_engine_per_test() -> AsyncIterator[None]:
    yield
    from core.cache.redis_client import reset_redis_client
    from core.database.session import dispose_engine

    await dispose_engine()
    await reset_redis_client()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    from core.security.session_validation import reset_session_validator
    from main import create_app

    transport = ASGITransport(app=create_app())
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
            yield async_client
    finally:
        reset_session_validator()


async def _setup(client: AsyncClient, tenants: list[uuid.UUID]) -> dict[str, Any]:
    await _seed_permissions()
    tenant_id = await _create_tenant()
    tenants.append(tenant_id)
    role_id = await _create_role(tenant_id, ALL_PERMISSION_CODES)
    _, email = await _create_user(tenant_id, role_ids=frozenset({role_id}))
    headers = await _login(client, email)
    return {"tenant_id": tenant_id, "headers": headers}


async def _create_client_(client: AsyncClient, headers: dict[str, str], name: str) -> uuid.UUID:
    resp = await client.post(
        "/api/v1/clients", headers=headers,
        json={"razao_social": name, "document": f"{uuid.uuid4().int % 10**14:014d}"},
    )
    assert resp.status_code == 201, resp.text
    return uuid.UUID(resp.json()["id"])


async def _create_driver(client: AsyncClient, headers: dict[str, str], name: str) -> uuid.UUID:
    resp = await client.post(
        "/api/v1/drivers", headers=headers,
        json={"nome": name, "cpf": f"{uuid.uuid4().int % 10**11:011d}", "employment_type": "EMPREGADO"},
    )
    assert resp.status_code == 201, resp.text
    return uuid.UUID(resp.json()["id"])


async def _create_vehicle(client: AsyncClient, headers: dict[str, str], plate: str, category_id: uuid.UUID) -> uuid.UUID:
    resp = await client.post(
        "/api/v1/veiculos", headers=headers,
        json={
            "plate": plate, "renavam": f"{uuid.uuid4().int % 10**11:011d}", "fabricante": "Volvo",
            "modelo": "FH 540", "ano_fabricacao": 2022, "categoria_id": str(category_id),
        },
    )
    assert resp.status_code == 201, resp.text
    return uuid.UUID(resp.json()["id"])


async def _create_supplier(client: AsyncClient, headers: dict[str, str], name: str) -> uuid.UUID:
    resp = await client.post(
        "/api/v1/suppliers", headers=headers,
        json={"razao_social": name, "cnpj": f"{uuid.uuid4().int % 10**14:014d}"},
    )
    assert resp.status_code == 201, resp.text
    return uuid.UUID(resp.json()["id"])


async def _create_cost_center(client: AsyncClient, headers: dict[str, str], name: str) -> uuid.UUID:
    resp = await client.post(
        "/api/v1/cost-centers", headers=headers,
        json={"accounting_code": f"CC-{uuid.uuid4().hex[:6]}", "nome": name},
    )
    assert resp.status_code == 201, resp.text
    return uuid.UUID(resp.json()["id"])


async def _create_chart_of_accounts(client: AsyncClient, headers: dict[str, str], name: str) -> uuid.UUID:
    resp = await client.post(
        "/api/v1/plano-contas", headers=headers,
        json={"account_code": f"PC-{uuid.uuid4().hex[:6]}", "name": name, "type": "DESPESA"},
    )
    assert resp.status_code == 201, resp.text
    return uuid.UUID(resp.json()["id"])


async def _create_trip(client: AsyncClient, headers: dict[str, str], client_id: uuid.UUID, scheduled: date) -> uuid.UUID:
    resp = await client.post(
        "/api/v1/viagens", headers=headers,
        json={"cliente_id": str(client_id), "data_programada": scheduled.isoformat()},
    )
    assert resp.status_code == 201, resp.text
    return uuid.UUID(resp.json()["id"])


async def _fixate_trip_financials(
    trip_id: uuid.UUID, *, driver_id: uuid.UUID, vehicle_id: uuid.UUID,
    predicted_revenue: Decimal, realized_revenue: Decimal, predicted_cost: Decimal, realized_cost: Decimal,
    cancelled: bool = False,
) -> None:
    """Simula o estado já-realizado de uma Viagem sem percorrer o pipeline fiscal/financeiro
    completo (ver docstring do módulo) — só o suficiente para testar a camada de agregação nova."""

    session_factory = get_session_factory()
    async with session_factory() as session:
        await session.execute(
            update(TripModel)
            .where(TripModel.id == trip_id)
            .values(
                motorista_id=driver_id, veiculo_tracionador_id=vehicle_id,
                receita_prevista_snapshot=predicted_revenue, receita_realizada=realized_revenue,
                custo_previsto=predicted_cost, custo_realizado=realized_cost,
                status_operacional="CANCELADA" if cancelled else "FINALIZADA",
            )
        )
        await session.commit()


async def _set_km_rodado(trip_id: uuid.UUID, value: Decimal | None) -> None:
    """V1 Operational Hardening, Parte 3 — simula `Trip.km_rodado` já calculado pelo pareamento de
    hodômetro (Parte 2), sem precisar percorrer despacho/encerramento reais aqui (já provado em
    `test_trip_odometer_km_realizado.py`) — só o suficiente para testar a agregação de KM."""

    session_factory = get_session_factory()
    async with session_factory() as session:
        await session.execute(update(TripModel).where(TripModel.id == trip_id).values(km_rodado=value))
        await session.commit()


async def _create_work_order(client: AsyncClient, headers: dict[str, str], vehicle_id: uuid.UUID) -> uuid.UUID:
    resp = await client.post(
        "/api/v1/ordens-servico", headers=headers,
        json={"tractor_unit_id": str(vehicle_id), "type": "CORRETIVA", "problem_description": "Vazamento de óleo."},
    )
    assert resp.status_code == 201, resp.text
    return uuid.UUID(resp.json()["id"])


async def _cancel_work_order(client: AsyncClient, headers: dict[str, str], work_order_id: uuid.UUID) -> None:
    resp = await client.post(
        f"/api/v1/ordens-servico/{work_order_id}/commands/cancelar", headers=headers,
        json={"justification": "Aberta por engano."},
    )
    assert resp.status_code == 200, resp.text


async def _create_payable(
    client: AsyncClient, headers: dict[str, str], *,
    supplier_id: uuid.UUID, cost_center_id: uuid.UUID, chart_of_accounts_id: uuid.UUID,
    origin: str, value: Decimal, competencia: date,
    maintenance_order_id: uuid.UUID | None = None, vehicle_id: uuid.UUID | None = None,
    driver_id: uuid.UUID | None = None,
) -> uuid.UUID:
    resp = await client.post(
        "/api/v1/contas-pagar", headers=headers,
        json={
            "supplier_id": str(supplier_id), "cost_center_id": str(cost_center_id), "origin": origin,
            "maintenance_order_id": str(maintenance_order_id) if maintenance_order_id else None,
            "vehicle_id": str(vehicle_id) if vehicle_id else None,
            "driver_id": str(driver_id) if driver_id else None,
            "value": str(value), "due_date": "2026-02-10", "accounting_period": competencia.isoformat(),
            "chart_of_accounts_id": str(chart_of_accounts_id),
        },
    )
    assert resp.status_code == 201, resp.text
    return uuid.UUID(resp.json()["id"])


async def _reject_payable(client: AsyncClient, headers: dict[str, str], payable_id: uuid.UUID) -> None:
    resp = await client.post(
        f"/api/v1/contas-pagar/{payable_id}/commands/reject", headers=headers,
        json={"justification": "Nota fiscal divergente."},
    )
    assert resp.status_code == 200, resp.text


@pytest.fixture
async def scenario(client: AsyncClient, tenants: list[uuid.UUID]) -> dict[str, Any]:
    ctx = await _setup(client, tenants)
    headers = ctx["headers"]

    client_a = await _create_client_(client, headers, f"Cliente A {uuid.uuid4().hex[:6]}")
    client_b = await _create_client_(client, headers, f"Cliente B {uuid.uuid4().hex[:6]}")
    driver_1 = await _create_driver(client, headers, f"Motorista 1 {uuid.uuid4().hex[:6]}")
    driver_2 = await _create_driver(client, headers, f"Motorista 2 {uuid.uuid4().hex[:6]}")
    category_id = await _seed_vehicle_category(ctx["tenant_id"])
    vehicle_1 = await _create_vehicle(client, headers, f"AAA{uuid.uuid4().hex[:4].upper()}", category_id)
    vehicle_2 = await _create_vehicle(client, headers, f"BBB{uuid.uuid4().hex[:4].upper()}", category_id)
    supplier_id = await _create_supplier(client, headers, f"Oficina {uuid.uuid4().hex[:6]}")
    cost_center_id = await _create_cost_center(client, headers, f"Frota {uuid.uuid4().hex[:6]}")
    chart_id = await _create_chart_of_accounts(client, headers, f"Manutenção {uuid.uuid4().hex[:6]}")

    period_date = date(2026, 1, 10)
    trip_1 = await _create_trip(client, headers, client_a, date(2026, 1, 5))
    trip_2 = await _create_trip(client, headers, client_a, date(2026, 1, 10))
    trip_3 = await _create_trip(client, headers, client_b, date(2026, 1, 15))
    trip_4_cancelled = await _create_trip(client, headers, client_a, date(2026, 1, 20))
    trip_5_out_of_period = await _create_trip(client, headers, client_a, date(2025, 6, 1))

    await _fixate_trip_financials(
        trip_1, driver_id=driver_1, vehicle_id=vehicle_1,
        predicted_revenue=Decimal("1000.00"), realized_revenue=Decimal("600.00"),
        predicted_cost=Decimal("400.00"), realized_cost=Decimal("300.00"),
    )
    await _fixate_trip_financials(
        trip_2, driver_id=driver_1, vehicle_id=vehicle_1,
        predicted_revenue=Decimal("1500.00"), realized_revenue=Decimal("400.00"),
        predicted_cost=Decimal("500.00"), realized_cost=Decimal("200.00"),
    )
    await _fixate_trip_financials(
        trip_3, driver_id=driver_2, vehicle_id=vehicle_2,
        predicted_revenue=Decimal("2000.00"), realized_revenue=Decimal("2000.00"),
        predicted_cost=Decimal("800.00"), realized_cost=Decimal("800.00"),
    )
    await _fixate_trip_financials(
        trip_4_cancelled, driver_id=driver_1, vehicle_id=vehicle_1,
        predicted_revenue=Decimal("9999.00"), realized_revenue=Decimal("9999.00"),
        predicted_cost=Decimal("1.00"), realized_cost=Decimal("1.00"), cancelled=True,
    )
    await _fixate_trip_financials(
        trip_5_out_of_period, driver_id=driver_1, vehicle_id=vehicle_1,
        predicted_revenue=Decimal("5000.00"), realized_revenue=Decimal("5000.00"),
        predicted_cost=Decimal("100.00"), realized_cost=Decimal("100.00"),
    )

    work_order_active = await _create_work_order(client, headers, vehicle_1)
    work_order_cancelled = await _create_work_order(client, headers, vehicle_1)
    await _cancel_work_order(client, headers, work_order_cancelled)

    # Manutenção real (V1): 1200 — dentro do período, não-REJEITADA, OS ativa.
    payable_maintenance = await _create_payable(
        client, headers, supplier_id=supplier_id, cost_center_id=cost_center_id, chart_of_accounts_id=chart_id,
        origin="ORDEM_SERVICO", value=Decimal("1200.00"), competencia=period_date,
        maintenance_order_id=work_order_active,
    )
    # OS cancelada: nunca deve contar, mesmo com CP lançada contra ela.
    await _create_payable(
        client, headers, supplier_id=supplier_id, cost_center_id=cost_center_id, chart_of_accounts_id=chart_id,
        origin="ORDEM_SERVICO", value=Decimal("999.00"), competencia=period_date,
        maintenance_order_id=work_order_cancelled,
    )
    # CP rejeitada: nunca deve contar, mesmo lançada contra a OS ativa.
    payable_rejected = await _create_payable(
        client, headers, supplier_id=supplier_id, cost_center_id=cost_center_id, chart_of_accounts_id=chart_id,
        origin="ORDEM_SERVICO", value=Decimal("5000.00"), competencia=period_date,
        maintenance_order_id=work_order_active,
    )
    await _reject_payable(client, headers, payable_rejected)
    # Outros Custos (V1): 150 — tagueado direto no Veículo, fora de Viagem/OS.
    await _create_payable(
        client, headers, supplier_id=supplier_id, cost_center_id=cost_center_id, chart_of_accounts_id=chart_id,
        origin="ABASTECIMENTO", value=Decimal("150.00"), competencia=period_date, vehicle_id=vehicle_1,
    )
    # Custo vinculado ao Motorista 1 — nunca deve aparecer no Veículo, só no Motorista.
    await _create_payable(
        client, headers, supplier_id=supplier_id, cost_center_id=cost_center_id, chart_of_accounts_id=chart_id,
        origin="AJUSTE_MANUAL", value=Decimal("80.00"), competencia=period_date, driver_id=driver_1,
    )

    return {
        "headers": headers, "client_a": client_a, "client_b": client_b, "driver_1": driver_1, "driver_2": driver_2,
        "vehicle_1": vehicle_1, "vehicle_2": vehicle_2, "trip_1": trip_1, "trip_2": trip_2, "trip_3": trip_3,
        "trip_4_cancelled": trip_4_cancelled, "trip_5_out_of_period": trip_5_out_of_period,
        "payable_maintenance": payable_maintenance,
        "period": {"data_programada__gte": "2026-01-01", "data_programada__lte": "2026-01-31"},
    }


async def test_overview_totals_never_double_count(client: AsyncClient, scenario: dict[str, Any]) -> None:
    resp = await client.get(
        "/api/v1/analytics/resultado-gerencial/visao-geral", headers=scenario["headers"], params=scenario["period"]
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    totals = body["totals"]

    assert totals["trips"] == 3
    assert Decimal(totals["realized_revenue"]) == Decimal("3000.00")
    assert Decimal(totals["predicted_revenue"]) == Decimal("4500.00")
    assert Decimal(body["maintenance_cost_realized"]) == Decimal("1200.00")
    assert Decimal(body["other_costs_realized"]) == Decimal("230.00")  # 150 (Veículo) + 80 (Motorista), somados 1x
    assert Decimal(totals["realized_cost"]) == Decimal("2730.00")  # 1300 (Viagens) + 1200 (Manutenção) + 230
    assert Decimal(totals["realized_margin"]) == Decimal("270.00")
    assert totals["realized_margin_pct"] == "9.00"
    assert totals["km"] is None  # gap registrado — nunca aproximado


async def test_overview_unfiltered_includes_out_of_period_trip(client: AsyncClient, scenario: dict[str, Any]) -> None:
    resp = await client.get("/api/v1/analytics/resultado-gerencial/visao-geral", headers=scenario["headers"])
    assert resp.status_code == 200, resp.text
    totals = resp.json()["totals"]
    assert totals["trips"] == 4  # 3 do período + a "fora do período" (trip_5), nunca a CANCELADA
    assert Decimal(totals["realized_revenue"]) == Decimal("8000.00")  # 3000 + 5000


async def test_trip_dimension_matches_source_fields_exactly(client: AsyncClient, scenario: dict[str, Any]) -> None:
    resp = await client.get(
        "/api/v1/analytics/resultado-gerencial/viagens", headers=scenario["headers"], params=scenario["period"]
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["meta"]["pagination"]["total"] == 3
    by_id = {row["trip_id"]: row for row in body["data"]}
    assert str(scenario["trip_1"]) in by_id
    row1 = by_id[str(scenario["trip_1"])]
    assert Decimal(row1["totals"]["realized_revenue"]) == Decimal("600.00")
    assert Decimal(row1["totals"]["realized_cost"]) == Decimal("300.00")
    assert Decimal(row1["totals"]["realized_margin"]) == Decimal("300.00")
    assert row1["totals"]["realized_margin_pct"] == "50.00"
    assert str(scenario["trip_4_cancelled"]) not in by_id
    assert str(scenario["trip_5_out_of_period"]) not in by_id


async def test_vehicle_dimension_distinguishes_operational_from_total_result(
    client: AsyncClient, scenario: dict[str, Any]
) -> None:
    resp = await client.get(
        "/api/v1/analytics/resultado-gerencial/veiculos", headers=scenario["headers"], params=scenario["period"]
    )
    assert resp.status_code == 200, resp.text
    by_id = {row["vehicle_id"]: row for row in resp.json()}
    v1 = by_id[str(scenario["vehicle_1"])]
    v2 = by_id[str(scenario["vehicle_2"])]

    # V1: ótimo operacionalmente (Resultado Operacional de Viagens = +500), mas a Manutenção fora de
    # viagem (1200) consome tudo e mais — Resultado Total vira negativo. Exatamente o cenário que o
    # usuário descreveu: "um caminhão pode aparentar excelente margem nas viagens e consumir R$20 mil
    # de manutenção fora delas".
    assert Decimal(v1["trip_cost_realized"]) == Decimal("500.00")
    assert Decimal(v1["operational_result"]) == Decimal("500.00")
    assert v1["operational_margin_pct"] == "50.00"
    assert Decimal(v1["maintenance_cost_realized"]) == Decimal("1200.00")
    assert Decimal(v1["other_costs_realized"]) == Decimal("150.00")
    assert Decimal(v1["totals"]["realized_cost"]) == Decimal("1850.00")  # 500 + 1200 + 150
    assert Decimal(v1["totals"]["realized_margin"]) == Decimal("-850.00")  # 1000 - 1850, Resultado Total < 0

    assert Decimal(v2["operational_result"]) == Decimal("1200.00")
    assert Decimal(v2["maintenance_cost_realized"]) == Decimal("0")
    assert Decimal(v2["totals"]["realized_margin"]) == Decimal("1200.00")  # sem custo fora de viagem, os dois batem

    # Soma dos Veículos == soma das Viagens no numerador de receita (toda Viagem do período tem
    # Veículo atribuído) — mas o custo realizado dos Veículos é MAIOR que o das Viagens em exatamente
    # a Manutenção + Outros Custos somados (1200 + 150 = 1350), nunca menos, nunca mais.
    vehicle_revenue_sum = sum(Decimal(v1["totals"]["realized_revenue"]) for v1 in by_id.values())
    assert vehicle_revenue_sum == Decimal("3000.00")


async def test_client_dimension_cost_scope_is_trip_only_and_sums_exactly(
    client: AsyncClient, scenario: dict[str, Any]
) -> None:
    resp = await client.get(
        "/api/v1/analytics/resultado-gerencial/clientes", headers=scenario["headers"], params=scenario["period"]
    )
    assert resp.status_code == 200, resp.text
    by_id = {row["client_id"]: row for row in resp.json()}
    client_a = by_id[str(scenario["client_a"])]
    client_b = by_id[str(scenario["client_b"])]

    assert Decimal(client_a["totals"]["realized_revenue"]) == Decimal("1000.00")
    assert Decimal(client_a["totals"]["realized_cost"]) == Decimal("500.00")  # só Custo Viagens — nunca Manutenção
    assert Decimal(client_b["totals"]["realized_revenue"]) == Decimal("2000.00")

    revenue_sum = sum(Decimal(c["totals"]["realized_revenue"]) for c in by_id.values())
    cost_sum = sum(Decimal(c["totals"]["realized_cost"]) for c in by_id.values())
    assert revenue_sum == Decimal("3000.00")
    assert cost_sum == Decimal("1300.00")  # == Σ Trip.custo_realizado exatamente — Cliente nunca soma Manutenção


async def test_driver_dimension_never_inherits_vehicle_maintenance(
    client: AsyncClient, scenario: dict[str, Any]
) -> None:
    resp = await client.get(
        "/api/v1/analytics/resultado-gerencial/motoristas", headers=scenario["headers"], params=scenario["period"]
    )
    assert resp.status_code == 200, resp.text
    by_id = {row["driver_id"]: row for row in resp.json()}
    driver_1 = by_id[str(scenario["driver_1"])]
    driver_2 = by_id[str(scenario["driver_2"])]

    # Motorista 1 dirigiu as Viagens do Veículo 1, cujo custo fora de viagem é R$1350 (Manutenção +
    # Outros Custos) — nada disso aparece aqui. Só o custo das Viagens dele (500) + o único lançamento
    # explicitamente vinculado a ele (AJUSTE_MANUAL de 80).
    assert Decimal(driver_1["trip_cost_realized"]) == Decimal("500.00")
    assert Decimal(driver_1["linked_cost_realized"]) == Decimal("80.00")
    assert Decimal(driver_1["totals"]["realized_cost"]) == Decimal("580.00")
    assert Decimal(driver_1["totals"]["realized_margin"]) == Decimal("420.00")  # 1000 - 580

    assert Decimal(driver_2["linked_cost_realized"]) == Decimal("0")
    assert Decimal(driver_2["totals"]["realized_cost"]) == Decimal("800.00")

    cost_sum = sum(Decimal(d["totals"]["realized_cost"]) for d in by_id.values())
    assert cost_sum == Decimal("1380.00")  # 1300 (Viagens) + 80 (vinculado) — nunca a Manutenção de 1200


async def test_vehicle_detail_drill_down_traces_cost_to_originating_payable(
    client: AsyncClient, scenario: dict[str, Any]
) -> None:
    resp = await client.get(
        f"/api/v1/analytics/resultado-gerencial/veiculos/{scenario['vehicle_1']}",
        headers=scenario["headers"], params=scenario["period"],
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert Decimal(body["result"]["totals"]["realized_cost"]) == Decimal("1850.00")
    trip_ids_in_detail = {t["trip_id"] for t in body["trips"]}
    assert str(scenario["trip_1"]) in trip_ids_in_detail
    assert str(scenario["trip_2"]) in trip_ids_in_detail
    cost_origin_ids = {c["accounts_payable_id"] for c in body["cost_origins"]}
    assert str(scenario["payable_maintenance"]) in cost_origin_ids
    # A CP rejeitada e a da OS cancelada nunca aparecem no drill-down — mesmo filtro da soma.
    assert len(body["cost_origins"]) == 2  # Manutenção (1200) + Outros Custos (150)


# ----------------------------------------------------------------------------------------------
# V1 Operational Hardening, Parte 3 — Resultado Gerencial por KM. `km_rodado` simulado direto (o
# pareamento de hodômetro real já está provado em `test_trip_odometer_km_realizado.py`) — aqui o
# que está sob teste é a agregação: nunca um `SUM()` parcial disfarçado de total.
# ----------------------------------------------------------------------------------------------


async def test_trip_km_metrics_available_when_km_rodado_is_known(
    client: AsyncClient, scenario: dict[str, Any]
) -> None:
    await _set_km_rodado(scenario["trip_3"], Decimal("400.00"))

    resp = await client.get(
        "/api/v1/analytics/resultado-gerencial/viagens", headers=scenario["headers"], params=scenario["period"]
    )
    assert resp.status_code == 200, resp.text
    row = next(r for r in resp.json()["data"] if r["trip_id"] == str(scenario["trip_3"]))
    totals = row["totals"]
    assert Decimal(totals["km"]) == Decimal("400.00")
    assert Decimal(totals["revenue_per_km"]) == Decimal("5.00")  # 2000 / 400
    assert Decimal(totals["cost_per_km"]) == Decimal("2.00")  # 800 / 400
    assert Decimal(totals["margin_per_km"]) == Decimal("3.00")  # 1200 / 400


async def test_trip_km_metrics_unavailable_when_km_rodado_is_null(
    client: AsyncClient, scenario: dict[str, Any]
) -> None:
    """Regra fundamental do usuário: sem KM, nunca estimar — `km`/`*_per_km` ficam `null`, nunca
    `0` (o que pareceria "sem receita/custo por km" em vez de "não sabemos")."""

    resp = await client.get(
        "/api/v1/analytics/resultado-gerencial/viagens", headers=scenario["headers"], params=scenario["period"]
    )
    assert resp.status_code == 200, resp.text
    row = next(r for r in resp.json()["data"] if r["trip_id"] == str(scenario["trip_1"]))
    totals = row["totals"]
    assert totals["km"] is None
    assert totals["revenue_per_km"] is None
    assert totals["cost_per_km"] is None
    assert totals["margin_per_km"] is None


async def test_vehicle_km_unavailable_when_only_some_trips_of_the_group_have_it(
    client: AsyncClient, scenario: dict[str, Any]
) -> None:
    """O caso central desta Parte: `SUM()` em SQL ignora `NULL` — sem essa correção, um Veículo com
    2 Viagens (só 1 com KM conhecido) mostraria o KM da única Viagem conhecida como se fosse o total
    do Veículo. V1 tem trip_1 (KM conhecido) + trip_2 (KM desconhecido) — o grupo inteiro precisa
    ficar "Indisponível", nunca uma soma parcial disfarçada de completa."""

    await _set_km_rodado(scenario["trip_1"], Decimal("300.00"))
    # trip_2 (mesmo Veículo V1) fica sem km_rodado — grupo incompleto.

    resp = await client.get(
        "/api/v1/analytics/resultado-gerencial/veiculos", headers=scenario["headers"], params=scenario["period"]
    )
    assert resp.status_code == 200, resp.text
    vehicle_1 = next(v for v in resp.json() if v["vehicle_id"] == str(scenario["vehicle_1"]))
    assert vehicle_1["totals"]["km"] is None
    assert vehicle_1["operational_cost_per_km"] is None
    assert vehicle_1["operational_result_per_km"] is None

    # Mas a Viagem individual (trip_1) continua mostrando o KM que ela de fato tem — o "Indisponível"
    # é só no agregado do Veículo, nunca inventado para esconder o dado que existe de verdade.
    trips_resp = await client.get(
        "/api/v1/analytics/resultado-gerencial/viagens", headers=scenario["headers"], params=scenario["period"]
    )
    trip_1_row = next(r for r in trips_resp.json()["data"] if r["trip_id"] == str(scenario["trip_1"]))
    assert Decimal(trip_1_row["totals"]["km"]) == Decimal("300.00")


async def test_vehicle_operational_cost_per_km_excludes_maintenance_total_includes_it(
    client: AsyncClient, scenario: dict[str, Any]
) -> None:
    """"Custo operacional/km" (só Viagens) vs. "Custo total/km" (`totals.cost_per_km`, inclui
    Manutenção+Outros Custos) — mesma distinção Operacional×Total já provada em R$, agora em KM."""

    await _set_km_rodado(scenario["trip_1"], Decimal("100.00"))
    await _set_km_rodado(scenario["trip_2"], Decimal("150.00"))
    # V1 completo: 250 km. Custo Viagens = 500 (300+200); Manutenção+Outros = 1350; Total = 1850.

    resp = await client.get(
        "/api/v1/analytics/resultado-gerencial/veiculos", headers=scenario["headers"], params=scenario["period"]
    )
    assert resp.status_code == 200, resp.text
    vehicle_1 = next(v for v in resp.json() if v["vehicle_id"] == str(scenario["vehicle_1"]))
    assert Decimal(vehicle_1["totals"]["km"]) == Decimal("250.00")
    assert Decimal(vehicle_1["operational_cost_per_km"]) == Decimal("2.00")  # 500 / 250 — só Viagens
    assert Decimal(vehicle_1["totals"]["cost_per_km"]) == Decimal("7.40")  # 1850 / 250 — Total
    assert Decimal(vehicle_1["operational_result_per_km"]) == Decimal("2.00")  # (1000-500) / 250
    assert Decimal(vehicle_1["totals"]["margin_per_km"]) == Decimal("-3.40")  # (1000-1850) / 250 — negativo
