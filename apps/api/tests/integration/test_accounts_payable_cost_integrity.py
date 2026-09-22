from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from core.database.session import get_session_factory
from core.multitenancy.context import reset_current_tenant_id, set_current_tenant_id
from modules.crm.infrastructure.persistence.models.client_model import ClientModel
from modules.financial.infrastructure.persistence.models.accounts_payable_model import (
    AccountsPayableModel,
    ExpenseAllocationModel,
    ExpenseApprovalModel,
    PayableStatusHistoryModel,
)
from modules.financial.infrastructure.persistence.models.chart_of_accounts_model import ChartOfAccountsModel
from modules.financial.infrastructure.persistence.models.cost_center_model import CostCenterModel
from modules.financial.infrastructure.persistence.models.financial_reversal_model import FinancialReversalModel
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
from modules.maintenance.infrastructure.persistence.models.supplier_model import SupplierModel
from modules.tenancy.infrastructure.persistence.models.tenant_model import TenantModel
from shared_kernel.domain.actor import AuthenticatedActor

pytestmark = pytest.mark.integration
"""V1 Operational Hardening, Parte 1 — Integridade do Custo Realizado. Prova a regra formalizada em
`docs/domain/006-financeiro.md` (Conta a Pagar): `Viagem.custo_realizado` é regime de competência
(qualquer status exceto `REJEITADA` conta, desde o lançamento) e que `RejectAccountsPayableHandler`
agora recalcula o custo da Viagem afetada — mesmo mecanismo de `DeleteAccountsPayableHandler`
(D390/D393). Também prova que Estorno (D266) nunca altera `custo_realizado` (não muda `status`/
`valor` do alvo) e que `GET /analytics/resultado-gerencial/viagens` reflete o valor já corrigido,
sem recomputar por conta própria."""

PASSWORD = "Senha-Forte-123"
ALCADA_PADRAO = Decimal("1000.00")

PERMISSION_CATALOG = [
    ("crm.client.create", "Criar clientes", "crm"),
    ("freight.trip.create", "Criar viagens", "freight"),
    ("freight.trip.view", "Ver viagens", "freight"),
    ("maintenance.supplier.create", "Criar fornecedores", "maintenance"),
    ("financial.cost_center.create", "Criar centros de custo", "financial"),
    ("financial.chart_of_accounts.create", "Criar plano de contas", "financial"),
    ("financial.payable.view", "Ver contas a pagar", "financial"),
    ("financial.payable.create", "Criar contas a pagar", "financial"),
    ("financial.payable.approve", "Aprovar contas a pagar", "financial"),
    ("financial.payable.reject", "Rejeitar contas a pagar", "financial"),
    ("financial.reversal.create", "Criar estornos financeiros", "financial"),
    ("financial.trip_actual_value.view", "Ver valores realizados da viagem", "financial"),
    ("analytics.freight_report.view", "Visualizar relatório de fretes", "analytics"),
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
                id=tenant_id, codigo=f"T-{tenant_id.hex[:8]}", versao=1, razao_social="Transportadora Custo LTDA",
                cnpj=f"{tenant_id.int % 10**14:014d}", status="ATIVO", criado_em=now, atualizado_em=now,
            )
        )
        await session.commit()
    return tenant_id


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
        await session.execute(delete(FinancialReversalModel).where(FinancialReversalModel.tenant_id == tenant_id))
        await session.execute(delete(ExpenseAllocationModel).where(ExpenseAllocationModel.tenant_id == tenant_id))
        await session.execute(delete(ExpenseApprovalModel).where(ExpenseApprovalModel.tenant_id == tenant_id))
        await session.execute(delete(PayableStatusHistoryModel).where(PayableStatusHistoryModel.tenant_id == tenant_id))
        await session.execute(delete(AccountsPayableModel).where(AccountsPayableModel.tenant_id == tenant_id))
        await session.execute(delete(TripModel).where(TripModel.tenant_id == tenant_id))
        await session.execute(delete(SupplierModel).where(SupplierModel.tenant_id == tenant_id))
        await session.execute(delete(CostCenterModel).where(CostCenterModel.tenant_id == tenant_id))
        await session.execute(delete(ChartOfAccountsModel).where(ChartOfAccountsModel.tenant_id == tenant_id))
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
    from core.database.session import dispose_engine

    await dispose_engine()


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


async def _create_client_(client: AsyncClient, headers: dict[str, str]) -> uuid.UUID:
    resp = await client.post(
        "/api/v1/clients", headers=headers,
        json={"razao_social": f"Cliente {uuid.uuid4().hex[:6]}", "document": f"{uuid.uuid4().int % 10**14:014d}"},
    )
    assert resp.status_code == 201, resp.text
    return uuid.UUID(resp.json()["id"])


async def _create_trip(client: AsyncClient, headers: dict[str, str], client_id: uuid.UUID) -> uuid.UUID:
    resp = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": str(client_id)})
    assert resp.status_code == 201, resp.text
    return uuid.UUID(resp.json()["id"])


async def _create_supplier(client: AsyncClient, headers: dict[str, str]) -> uuid.UUID:
    resp = await client.post(
        "/api/v1/suppliers", headers=headers,
        json={"razao_social": f"Fornecedor {uuid.uuid4().hex[:6]}", "cnpj": f"{uuid.uuid4().int % 10**14:014d}"},
    )
    assert resp.status_code == 201, resp.text
    return uuid.UUID(resp.json()["id"])


async def _create_cost_center(client: AsyncClient, headers: dict[str, str]) -> uuid.UUID:
    resp = await client.post(
        "/api/v1/cost-centers", headers=headers,
        json={"accounting_code": f"CC-{uuid.uuid4().hex[:6]}", "nome": f"Centro {uuid.uuid4().hex[:6]}"},
    )
    assert resp.status_code == 201, resp.text
    return uuid.UUID(resp.json()["id"])


async def _create_chart_of_accounts(client: AsyncClient, headers: dict[str, str]) -> uuid.UUID:
    resp = await client.post(
        "/api/v1/plano-contas", headers=headers,
        json={"account_code": f"PC-{uuid.uuid4().hex[:6]}", "name": f"Conta {uuid.uuid4().hex[:6]}", "type": "DESPESA"},
    )
    assert resp.status_code == 201, resp.text
    return uuid.UUID(resp.json()["id"])


async def _create_trip_payable(
    client: AsyncClient, headers: dict[str, str], *,
    trip_id: uuid.UUID, supplier_id: uuid.UUID, cost_center_id: uuid.UUID, chart_id: uuid.UUID, value: str,
) -> uuid.UUID:
    resp = await client.post(
        "/api/v1/contas-pagar", headers=headers,
        json={
            "supplier_id": str(supplier_id), "cost_center_id": str(cost_center_id), "origin": "VIAGEM",
            "trip_id": str(trip_id), "value": value, "due_date": "2026-12-01", "accounting_period": "2026-11-01",
            "chart_of_accounts_id": str(chart_id),
        },
    )
    assert resp.status_code == 201, resp.text
    return uuid.UUID(resp.json()["id"])


async def _get_actual_cost(client: AsyncClient, headers: dict[str, str], trip_id: uuid.UUID) -> Decimal | None:
    resp = await client.get(f"/api/v1/viagens/{trip_id}/financeiro", headers=headers)
    assert resp.status_code == 200, resp.text
    value = resp.json()["actual_cost"]
    return Decimal(value) if value is not None else None


@pytest.fixture
async def scenario(client: AsyncClient, tenants: list[uuid.UUID]) -> dict[str, Any]:
    ctx = await _setup(client, tenants)
    headers = ctx["headers"]
    client_id = await _create_client_(client, headers)
    trip_id = await _create_trip(client, headers, client_id)
    supplier_id = await _create_supplier(client, headers)
    cost_center_id = await _create_cost_center(client, headers)
    chart_id = await _create_chart_of_accounts(client, headers)
    return {
        "headers": headers, "client_id": client_id, "trip_id": trip_id, "supplier_id": supplier_id,
        "cost_center_id": cost_center_id, "chart_id": chart_id,
    }


async def test_rejecting_a_payable_removes_its_contribution_from_realized_cost(
    client: AsyncClient, scenario: dict[str, Any]
) -> None:
    """O caso central do gap: uma Conta a Pagar `AGUARDANDO_APROVACAO` já conta em
    `custo_realizado` desde o lançamento (regime de competência) — rejeitá-la precisa remover essa
    contribuição, nunca deixar o valor "fantasma" no custo da Viagem."""

    trip_id, headers = scenario["trip_id"], scenario["headers"]

    await _create_trip_payable(
        client, headers, trip_id=trip_id, supplier_id=scenario["supplier_id"],
        cost_center_id=scenario["cost_center_id"], chart_id=scenario["chart_id"], value="300.00",
    )
    await _create_trip_payable(
        client, headers, trip_id=trip_id, supplier_id=scenario["supplier_id"],
        cost_center_id=scenario["cost_center_id"], chart_id=scenario["chart_id"], value="200.00",
    )
    assert await _get_actual_cost(client, headers, trip_id) == Decimal("500.00")

    # Acima da alçada (1000.00) — nasce AGUARDANDO_APROVACAO, mas já conta (accrual).
    payable_3 = await _create_trip_payable(
        client, headers, trip_id=trip_id, supplier_id=scenario["supplier_id"],
        cost_center_id=scenario["cost_center_id"], chart_id=scenario["chart_id"], value="1500.00",
    )
    payable_3_status = (await client.get(f"/api/v1/contas-pagar/{payable_3}", headers=headers)).json()["status"]
    assert payable_3_status == "AGUARDANDO_APROVACAO"
    assert await _get_actual_cost(client, headers, trip_id) == Decimal("2000.00")  # 300+200+1500

    reject = await client.post(
        f"/api/v1/contas-pagar/{payable_3}/commands/reject", headers=headers,
        json={"justification": "Nota fiscal divergente do valor lançado."},
    )
    assert reject.status_code == 200, reject.text
    assert reject.json()["status"] == "REJEITADA"

    # O fantasma de 1500 desaparece — volta exatamente ao que payable_1+payable_2 somam, nunca menos
    # (perderia custo válido), nunca mais (a rejeição não gera dinheiro).
    assert await _get_actual_cost(client, headers, trip_id) == Decimal("500.00")

    # Resultado Gerencial lê o mesmo valor já corrigido — nunca recomputa por conta própria.
    results = await client.get(
        "/api/v1/analytics/resultado-gerencial/viagens", headers=headers, params={"limit": 50}
    )
    assert results.status_code == 200, results.text
    row = next(r for r in results.json()["data"] if r["trip_id"] == str(trip_id))
    assert Decimal(row["totals"]["realized_cost"]) == Decimal("500.00")

    # Rejeitar de novo é impossível — a transição exige AGUARDANDO_APROVACAO.
    reject_again = await client.post(
        f"/api/v1/contas-pagar/{payable_3}/commands/reject", headers=headers,
        json={"justification": "Tentativa duplicada."},
    )
    assert reject_again.status_code == 409
    assert reject_again.json()["error"]["code"] == "FINANCIAL_PAYABLE_INVALID_TRANSITION"
    assert await _get_actual_cost(client, headers, trip_id) == Decimal("500.00")


async def test_approved_and_paid_payables_are_not_rejectable_and_keep_counting(
    client: AsyncClient, scenario: dict[str, Any]
) -> None:
    """Regra formal: qualquer status exceto `REJEITADA` conta — `approve`/`pay` nunca precisam
    "ativar" o custo, ele já contava desde o lançamento; e uma Conta a Pagar já `APROVADA` não pode
    ser rejeitada diretamente (a transição só existe a partir de `AGUARDANDO_APROVACAO`)."""

    trip_id, headers = scenario["trip_id"], scenario["headers"]

    payable = await _create_trip_payable(
        client, headers, trip_id=trip_id, supplier_id=scenario["supplier_id"],
        cost_center_id=scenario["cost_center_id"], chart_id=scenario["chart_id"], value="400.00",
    )
    status = (await client.get(f"/api/v1/contas-pagar/{payable}", headers=headers)).json()["status"]
    assert status == "APROVADA"  # abaixo da alçada — aprovação automática
    assert await _get_actual_cost(client, headers, trip_id) == Decimal("400.00")

    cannot_reject = await client.post(
        f"/api/v1/contas-pagar/{payable}/commands/reject", headers=headers, json={"justification": "Tentativa."}
    )
    assert cannot_reject.status_code == 409
    assert cannot_reject.json()["error"]["code"] == "FINANCIAL_PAYABLE_INVALID_TRANSITION"
    assert await _get_actual_cost(client, headers, trip_id) == Decimal("400.00")


async def test_reversal_never_changes_realized_cost(client: AsyncClient, scenario: dict[str, Any]) -> None:
    """D266: Estorno é só um registro de correção — nunca altera `status`/`valor` do alvo. Prova que
    `custo_realizado` continua exatamente o mesmo antes e depois do Estorno, e que a Conta a Pagar
    original permanece com seu status original."""

    trip_id, headers = scenario["trip_id"], scenario["headers"]

    payable = await _create_trip_payable(
        client, headers, trip_id=trip_id, supplier_id=scenario["supplier_id"],
        cost_center_id=scenario["cost_center_id"], chart_id=scenario["chart_id"], value="600.00",
    )
    assert await _get_actual_cost(client, headers, trip_id) == Decimal("600.00")

    reversal = await client.post(
        "/api/v1/estornos-financeiros", headers=headers,
        json={"accounts_payable_id": str(payable), "value": "600.00", "reason": "Lançamento em duplicidade."},
    )
    assert reversal.status_code == 201, reversal.text

    # Nem o status nem o valor da Conta a Pagar mudam — e portanto nem o custo_realizado.
    payable_after = (await client.get(f"/api/v1/contas-pagar/{payable}", headers=headers)).json()
    assert payable_after["status"] == "APROVADA"
    assert Decimal(payable_after["value"]) == Decimal("600.00")
    assert await _get_actual_cost(client, headers, trip_id) == Decimal("600.00")
