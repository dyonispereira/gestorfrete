from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select, text

from core.database.session import get_session_factory
from core.multitenancy.context import reset_current_tenant_id, set_current_tenant_id
from modules.crm.infrastructure.persistence.models.client_model import ClientModel
from modules.documents.infrastructure.persistence.models.cte_model import CteModel, CteStatusHistoryModel
from modules.documents.infrastructure.persistence.models.fiscal_configuration_model import (
    FiscalConfigurationModel,
)
from modules.drivers.infrastructure.persistence.models.driver_model import DriverModel
from modules.financial.domain.value_objects.payment_method_status import PaymentMethodStatus
from modules.financial.infrastructure.persistence.models.accounts_payable_model import (
    AccountsPayableModel,
    ExpenseAllocationModel,
    ExpenseApprovalModel,
    PayableStatusHistoryModel,
)
from modules.financial.infrastructure.persistence.models.accounts_receivable_model import (
    AccountsReceivableModel,
    ReceivableStatusHistoryModel,
)
from modules.financial.infrastructure.persistence.models.bank_account_model import BankAccountModel
from modules.financial.infrastructure.persistence.models.chart_of_accounts_model import ChartOfAccountsModel
from modules.financial.infrastructure.persistence.models.cost_center_model import CostCenterModel
from modules.financial.infrastructure.persistence.models.financial_reversal_model import FinancialReversalModel
from modules.financial.infrastructure.persistence.models.invoice_model import InvoiceModel
from modules.financial.infrastructure.persistence.models.payment_method_model import PaymentMethodModel
from modules.fleet.infrastructure.persistence.models.vehicle_category_model import VehicleCategoryModel
from modules.fleet.infrastructure.persistence.models.vehicle_model import VehicleModel
from modules.freight.application.trip_internal_transitions import TripInternalTransitions
from modules.freight.domain.value_objects.trip_fiscal_status import TripFiscalStatus
from modules.freight.infrastructure.persistence.models.delivery_model import DeliveryModel, DeliveryWindowModel
from modules.freight.infrastructure.persistence.models.occurrence_model import OccurrenceModel
from modules.freight.infrastructure.persistence.models.proof_of_delivery_model import ProofOfDeliveryModel
from modules.freight.infrastructure.persistence.models.trip_allocation_model import TripAllocationModel
from modules.freight.infrastructure.persistence.models.trip_model import TripModel
from modules.freight.infrastructure.persistence.models.trip_status_history_model import TripStatusHistoryModel
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
from shared.collaboration.infrastructure.persistence.models.attachment_model import AttachmentModel
from shared.collaboration.infrastructure.persistence.models.comment_model import CommentModel
from shared_kernel.domain.actor import AuthenticatedActor

pytestmark = pytest.mark.integration
"""Sprint 11, Lote 6 — Financeiro (D384-D394). D352 aplicado aos agregados `ChartOfAccounts`/
`BankAccount`/`AccountsPayable`/`Invoice`/`AccountsReceivable`/`FinancialReversal`, mais as quatro
auditorias explicitamente pedidas pelo usuário: (1) totais derivados por agregação (`Trip.
custo_realizado`/`.receita_realizada`) nunca editáveis diretamente, só via criar/remover Conta a
Pagar/confirmar recebimento; (2) toda mudança relevante de status gera exatamente um registro em
`*_status_history`, sem transições silenciosas — incluindo a derivada `LANCADA→APROVADA/AGUARDANDO_
APROVACAO`; (3) Estorno nunca reverte o estado original; (4) permissões por campo em `GET /viagens/
{id}/financeiro` (D267-style, primeiro uso significativo neste backend)."""

PASSWORD = "Senha-Forte-123"
ALCADA_PADRAO = Decimal("1000.00")

PERMISSION_CATALOG = [
    ("freight.trip.view", "Ver viagens", "freight"),
    ("freight.trip.create", "Criar viagens", "freight"),
    ("freight.trip.edit", "Editar viagens", "freight"),
    ("freight.trip.dispatch", "Despachar viagem", "freight"),
    ("freight.delivery.view", "Ver entregas", "freight"),
    ("freight.delivery.create", "Criar entregas", "freight"),
    ("freight.delivery.edit", "Editar entregas", "freight"),
    ("freight.pod.create", "Registrar canhoto", "freight"),
    ("crm.client.create", "Criar clientes", "crm"),
    ("drivers.driver.create", "Criar motoristas", "drivers"),
    ("fleet.vehicle.create", "Criar veículos", "fleet"),
    ("maintenance.supplier.create", "Criar fornecedores", "maintenance"),
    ("financial.cost_center.view", "Ver centros de custo", "financial"),
    ("financial.cost_center.create", "Criar centros de custo", "financial"),
    ("financial.chart_of_accounts.view", "Ver plano de contas", "financial"),
    ("financial.chart_of_accounts.create", "Criar plano de contas", "financial"),
    ("financial.chart_of_accounts.edit", "Editar plano de contas", "financial"),
    ("financial.chart_of_accounts.delete", "Excluir plano de contas", "financial"),
    ("financial.bank_account.view", "Ver contas bancárias", "financial"),
    ("financial.bank_account.create", "Criar contas bancárias", "financial"),
    ("financial.bank_account.edit", "Editar contas bancárias", "financial"),
    ("financial.bank_account.delete", "Excluir contas bancárias", "financial"),
    ("financial.payable.view", "Ver contas a pagar", "financial"),
    ("financial.payable.create", "Criar contas a pagar", "financial"),
    ("financial.payable.edit", "Editar contas a pagar", "financial"),
    ("financial.payable.approve", "Aprovar contas a pagar", "financial"),
    ("financial.payable.reject", "Rejeitar contas a pagar", "financial"),
    ("financial.payable.pay", "Pagar contas a pagar", "financial"),
    ("financial.cost_allocation.view", "Ver rateios de despesa", "financial"),
    ("financial.invoice.view", "Ver faturas", "financial"),
    ("financial.invoice.create", "Criar faturas", "financial"),
    ("financial.invoice.cancel", "Cancelar faturas", "financial"),
    ("financial.receivable.view", "Ver contas a receber", "financial"),
    ("financial.receivable.create", "Criar contas a receber", "financial"),
    ("financial.receivable.edit", "Editar contas a receber", "financial"),
    ("financial.receivable.confirm_receipt", "Confirmar recebimento", "financial"),
    ("financial.reversal.view", "Ver estornos financeiros", "financial"),
    ("financial.reversal.create", "Criar estornos financeiros", "financial"),
    ("financial.trip_predicted_value.view", "Ver valores previstos da viagem", "financial"),
    ("financial.trip_actual_value.view", "Ver valores realizados da viagem", "financial"),
    ("financial.trip_margin.view", "Ver margem da viagem", "financial"),
]
ALL_PERMISSION_CODES = [c for c, _, _ in PERMISSION_CATALOG]


async def _seed_permissions() -> dict[str, uuid.UUID]:
    session_factory = get_session_factory()
    now = datetime.now(timezone.utc)
    ids: dict[str, uuid.UUID] = {}
    async with session_factory() as session:
        for codigo, nome, modulo in PERMISSION_CATALOG:
            existing = (
                await session.execute(select(PermissionModel).where(PermissionModel.codigo == codigo))
            ).scalar_one_or_none()
            if existing is None:
                model = PermissionModel(id=uuid.uuid4(), codigo=codigo, nome=nome, modulo=modulo, criado_em=now)
                session.add(model)
                await session.flush()
                ids[codigo] = model.id
            else:
                ids[codigo] = existing.id
        await session.commit()
    return ids


async def _create_tenant() -> uuid.UUID:
    session_factory = get_session_factory()
    now = datetime.now(timezone.utc)
    tenant_id = uuid.uuid4()
    async with session_factory() as session:
        session.add(
            TenantModel(
                id=tenant_id, codigo=f"T-{tenant_id.hex[:8]}", versao=1, razao_social="Transportadora de Teste LTDA",
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


async def _seed_payment_method(tenant_id: uuid.UUID) -> uuid.UUID:
    """D386 — `formas_pagamento` não tem endpoint HTTP; seed direto via Repository, mesmo padrão de
    `VehicleCategory` (D363)."""

    session_factory = get_session_factory()
    method_id = uuid.uuid4()
    async with session_factory() as session:
        session.add(
            PaymentMethodModel(
                id=method_id, tenant_id=tenant_id, nome=f"Boleto {method_id.hex[:6]}",
                status=PaymentMethodStatus.ATIVA.value,
            )
        )
        await session.commit()
    return method_id


async def _seed_fiscal_configuration(tenant_id: uuid.UUID) -> None:
    """D396 (Lote 7) — despachar uma Viagem agora cria um CT-e automaticamente, o que exige uma
    `FiscalConfiguration` para o tenant. Seed direto via Repository, mesmo padrão de `PaymentMethod`
    (D386)."""

    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(
            FiscalConfigurationModel(
                id=uuid.uuid4(), tenant_id=tenant_id, certificado_arquivo_id=uuid.uuid4(),
                certificado_validade=date(2030, 1, 1), ambiente="HOMOLOGACAO", regime_tributario="SIMPLES",
                serie_cte="1", proximo_numero_cte=1, serie_mdfe="1", proximo_numero_mdfe=1, status="ATIVA",
            )
        )
        await session.commit()


async def _create_role(tenant_id: uuid.UUID, permission_codes: list[str]) -> uuid.UUID:
    bootstrap_actor = AuthenticatedActor(user_id=uuid.uuid4(), tenant_id=tenant_id, session_id=uuid.uuid4())
    token = set_current_tenant_id(tenant_id)
    try:
        dto = await CreateRoleHandler().handle(
            CreateRoleCommand(actor=bootstrap_actor, nome=f"Papel-{uuid.uuid4().hex[:8]}", descricao=None, permission_codes=permission_codes)
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


async def _actor_with_permissions(
    client: AsyncClient, tenants: list[uuid.UUID], permission_codes: list[str]
) -> tuple[dict[str, str], uuid.UUID]:
    tenant_id = await _create_tenant()
    tenants.append(tenant_id)
    role_id = await _create_role(tenant_id, permission_codes)
    _, email = await _create_user(tenant_id, role_ids=frozenset({role_id}))
    headers = await _login(client, email)
    return headers, tenant_id


async def _full_access_actor(client: AsyncClient, tenants: list[uuid.UUID]) -> tuple[dict[str, str], uuid.UUID, uuid.UUID]:
    """Retorna (headers, tenant_id, category_id)."""

    headers, tenant_id = await _actor_with_permissions(client, tenants, ALL_PERMISSION_CODES)
    category_id = await _seed_vehicle_category(tenant_id)
    await _seed_fiscal_configuration(tenant_id)
    return headers, tenant_id, category_id


async def _cleanup_tenant(tenant_id: uuid.UUID) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user_ids = (await session.execute(select(UserModel.id).where(UserModel.tenant_id == tenant_id))).scalars().all()
        role_ids = (await session.execute(select(RoleModel.id).where(RoleModel.tenant_id == tenant_id))).scalars().all()
        entrega_ids = (
            await session.execute(select(DeliveryModel.id).where(DeliveryModel.tenant_id == tenant_id))
        ).scalars().all()

        await session.execute(delete(SessionModel).where(SessionModel.tenant_id == tenant_id))
        if user_ids:
            await session.execute(delete(usuarios_papeis).where(usuarios_papeis.c.usuario_id.in_(user_ids)))
        if role_ids:
            await session.execute(delete(papel_permissao).where(papel_permissao.c.papel_id.in_(role_ids)))
        await session.execute(delete(AttachmentModel).where(AttachmentModel.tenant_id == tenant_id))
        await session.execute(delete(CommentModel).where(CommentModel.tenant_id == tenant_id))

        # Financeiro — ordem de FK: filhos antes dos pais.
        await session.execute(delete(FinancialReversalModel).where(FinancialReversalModel.tenant_id == tenant_id))
        await session.execute(
            delete(ReceivableStatusHistoryModel).where(ReceivableStatusHistoryModel.tenant_id == tenant_id)
        )
        await session.execute(delete(AccountsReceivableModel).where(AccountsReceivableModel.tenant_id == tenant_id))
        await session.execute(delete(InvoiceModel).where(InvoiceModel.tenant_id == tenant_id))
        await session.execute(delete(ExpenseAllocationModel).where(ExpenseAllocationModel.tenant_id == tenant_id))
        await session.execute(delete(ExpenseApprovalModel).where(ExpenseApprovalModel.tenant_id == tenant_id))
        await session.execute(
            delete(PayableStatusHistoryModel).where(PayableStatusHistoryModel.tenant_id == tenant_id)
        )
        await session.execute(delete(AccountsPayableModel).where(AccountsPayableModel.tenant_id == tenant_id))
        await session.execute(delete(BankAccountModel).where(BankAccountModel.tenant_id == tenant_id))
        await session.execute(delete(ChartOfAccountsModel).where(ChartOfAccountsModel.tenant_id == tenant_id))
        await session.execute(delete(PaymentMethodModel).where(PaymentMethodModel.tenant_id == tenant_id))
        await session.execute(delete(CostCenterModel).where(CostCenterModel.tenant_id == tenant_id))
        await session.execute(delete(SupplierModel).where(SupplierModel.tenant_id == tenant_id))

        if entrega_ids:
            await session.execute(delete(ProofOfDeliveryModel).where(ProofOfDeliveryModel.entrega_id.in_(entrega_ids)))
            await session.execute(delete(DeliveryWindowModel).where(DeliveryWindowModel.entrega_id.in_(entrega_ids)))
        await session.execute(delete(OccurrenceModel).where(OccurrenceModel.tenant_id == tenant_id))
        await session.execute(delete(DeliveryModel).where(DeliveryModel.tenant_id == tenant_id))
        await session.execute(delete(TripAllocationModel).where(TripAllocationModel.tenant_id == tenant_id))
        await session.execute(delete(TripStatusHistoryModel).where(TripStatusHistoryModel.tenant_id == tenant_id))
        # D396 (Lote 7) — despachar cria um CT-e automaticamente (`ctes.viagem_id` FK); precisa
        # sair antes de `TripModel`.
        await session.execute(delete(CteStatusHistoryModel).where(CteStatusHistoryModel.tenant_id == tenant_id))
        await session.execute(delete(CteModel).where(CteModel.tenant_id == tenant_id))
        await session.execute(delete(FiscalConfigurationModel).where(FiscalConfigurationModel.tenant_id == tenant_id))
        await session.execute(delete(TripModel).where(TripModel.tenant_id == tenant_id))
        await session.execute(delete(VehicleModel).where(VehicleModel.tenant_id == tenant_id))
        await session.execute(delete(VehicleCategoryModel).where(VehicleCategoryModel.tenant_id == tenant_id))
        await session.execute(delete(DriverModel).where(DriverModel.tenant_id == tenant_id))
        await session.execute(delete(ClientModel).where(ClientModel.tenant_id == tenant_id))
        await session.execute(delete(UserModel).where(UserModel.tenant_id == tenant_id))
        await session.execute(delete(RoleModel).where(RoleModel.tenant_id == tenant_id))
        await session.execute(delete(TenantModel).where(TenantModel.id == tenant_id))
        await session.commit()


@pytest.fixture
async def permission_ids() -> dict[str, uuid.UUID]:
    return await _seed_permissions()


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


# --------------------------------------------------------------------------------------
# Helpers de domínio (Cadastros/Operação já existentes, reaproveitados como pré-requisito)
# --------------------------------------------------------------------------------------


async def _create_client_entity(client: AsyncClient, headers: dict[str, str]) -> str:
    resp = await client.post(
        "/api/v1/clients", headers=headers,
        json={"razao_social": "Cliente de Teste LTDA", "document": f"{uuid.uuid4().int % 10**11:011d}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _create_driver(client: AsyncClient, headers: dict[str, str]) -> str:
    resp = await client.post(
        "/api/v1/drivers", headers=headers,
        json={"nome": "Motorista de Teste", "cpf": f"{uuid.uuid4().int % 10**11:011d}", "employment_type": "EMPREGADO"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _create_vehicle(client: AsyncClient, headers: dict[str, str], category_id: uuid.UUID) -> str:
    resp = await client.post(
        "/api/v1/veiculos", headers=headers,
        json={
            "plate": f"VG{uuid.uuid4().hex[:5].upper()}", "renavam": f"{uuid.uuid4().int % 10**11:011d}",
            "fabricante": "Volvo", "modelo": "FH540", "ano_fabricacao": 2022, "categoria_id": str(category_id),
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _create_supplier(client: AsyncClient, headers: dict[str, str]) -> str:
    resp = await client.post(
        "/api/v1/suppliers", headers=headers,
        json={"razao_social": "Fornecedor de Teste LTDA", "cnpj": f"{uuid.uuid4().int % 10**14:014d}"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _create_cost_center(client: AsyncClient, headers: dict[str, str]) -> str:
    resp = await client.post(
        "/api/v1/cost-centers", headers=headers,
        json={"accounting_code": f"CC-{uuid.uuid4().hex[:6]}", "nome": "Centro de Custo de Teste"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _create_chart_of_accounts(
    client: AsyncClient, headers: dict[str, str], *, type_: str = "DESPESA", parent_id: str | None = None
) -> str:
    body: dict[str, object] = {"account_code": f"CTA-{uuid.uuid4().hex[:8]}", "name": "Conta de Teste", "type": type_}
    if parent_id is not None:
        body["parent_id"] = parent_id
    resp = await client.post("/api/v1/plano-contas", headers=headers, json=body)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _create_bank_account(client: AsyncClient, headers: dict[str, str]) -> str:
    resp = await client.post(
        "/api/v1/contas-bancarias", headers=headers,
        json={"bank": "Banco de Teste", "branch": "0001", "account_number": f"{uuid.uuid4().int % 10**8:08d}", "type": "CORRENTE"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _allocate_and_plan(client: AsyncClient, headers: dict[str, str], trip_id: str, driver_id: str, vehicle_id: str) -> None:
    resp = await client.post(
        f"/api/v1/viagens/{trip_id}/resources", headers=headers,
        json={"driver_id": driver_id, "tractor_unit_id": vehicle_id},
    )
    assert resp.status_code == 201, resp.text


async def _advance_to_em_entrega(client: AsyncClient, headers: dict[str, str], tenant_id: uuid.UUID, trip_id: str) -> str:
    """Reproduz `_advance_to_em_entrega` do Lote 5 (D376) — devolve o `delivery_id` criado."""

    simulator = TripInternalTransitions()
    now = datetime.now(timezone.utc)
    token = set_current_tenant_id(tenant_id)
    try:
        await simulator.await_checklist(trip_id=uuid.UUID(trip_id), now=now)
        await simulator.approve_checklist(trip_id=uuid.UUID(trip_id), now=now)
    finally:
        reset_current_tenant_id(token)

    dispatch_resp = await client.post(f"/api/v1/viagens/{trip_id}/commands/dispatch", headers=headers)
    assert dispatch_resp.status_code == 200, dispatch_resp.text

    delivery_resp = await client.post(
        f"/api/v1/viagens/{trip_id}/entregas", headers=headers,
        json={"order": 1, "recipient": "Fulano de Tal", "delivery_address": {"cidade": "São Paulo"}},
    )
    assert delivery_resp.status_code == 201, delivery_resp.text
    delivery_id = delivery_resp.json()["id"]

    token = set_current_tenant_id(tenant_id)
    try:
        await simulator.register_collection(trip_id=uuid.UUID(trip_id), now=now)
        await simulator.confirm_manifest(trip_id=uuid.UUID(trip_id), now=now)
    finally:
        reset_current_tenant_id(token)

    return delivery_id


async def _prepare_invoiceable_trip(
    client: AsyncClient, headers: dict[str, str], tenant_id: uuid.UUID, category_id: uuid.UUID
) -> tuple[str, str]:
    """Viagem com ao menos um Canhoto registrado e `status_fiscal = CTE_EMITIDO` — a precondição
    real de `POST /faturas` (D388). Retorna `(trip_id, delivery_id)`."""

    client_id = await _create_client_entity(client, headers)
    driver_id = await _create_driver(client, headers)
    vehicle_id = await _create_vehicle(client, headers, category_id)

    create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
    assert create.status_code == 201, create.text
    trip_id = create.json()["id"]
    await _allocate_and_plan(client, headers, trip_id, driver_id, vehicle_id)
    delivery_id = await _advance_to_em_entrega(client, headers, tenant_id, trip_id)

    canhoto = await client.post(f"/api/v1/viagens/{trip_id}/entregas/{delivery_id}/canhoto", headers=headers, json={})
    assert canhoto.status_code == 201, canhoto.text

    token = set_current_tenant_id(tenant_id)
    try:
        await TripInternalTransitions().record_fiscal_transition(
            trip_id=uuid.UUID(trip_id), status=TripFiscalStatus.CTE_EMITIDO, now=datetime.now(timezone.utc)
        )
    finally:
        reset_current_tenant_id(token)

    return trip_id, delivery_id


async def _force_payable_status(payable_id: str, status: str) -> None:
    """Flip direto de `status` para `LANCADA` — `AccountsPayable.create()` deriva a alçada de forma
    instantânea (`accounts_payable.py`), então `status = LANCADA` nunca fica observável via HTTP.
    `PATCH`/`DELETE` só são exercitáveis em `LANCADA`; sem essa manipulação de teste, os dois
    endpoints seriam código morto — mesmo espírito de `TripInternalTransitions` (D376): simula uma
    precondição que a máquina de estados real não deixa alcançar via API neste lote."""

    session_factory = get_session_factory()
    async with session_factory() as session:
        await session.execute(
            text("UPDATE contas_pagar SET status = :status WHERE id = :id"), {"status": status, "id": payable_id}
        )
        await session.commit()


class TestChartOfAccountsFlow:
    async def test_crud_and_cycle_detection(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, _ = await _full_access_actor(client, tenants)

        create = await client.post(
            "/api/v1/plano-contas", headers=headers,
            json={"account_code": "1", "name": "Despesas Operacionais", "type": "DESPESA"},
        )
        assert create.status_code == 201, create.text
        account_id = create.json()["id"]
        assert create.json()["status"] == "ATIVO"

        get_resp = await client.get(f"/api/v1/plano-contas/{account_id}", headers=headers)
        assert get_resp.status_code == 200

        list_resp = await client.get("/api/v1/plano-contas", headers=headers)
        assert list_resp.status_code == 200
        assert any(a["id"] == account_id for a in list_resp.json()["data"])

        patch_resp = await client.patch(
            f"/api/v1/plano-contas/{account_id}", headers=headers, json={"name": "Despesas Operacionais Renomeada"}
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["name"] == "Despesas Operacionais Renomeada"

        self_cycle = await client.patch(f"/api/v1/plano-contas/{account_id}", headers=headers, json={"parent_id": account_id})
        assert self_cycle.status_code == 422, self_cycle.text
        assert self_cycle.json()["error"]["code"] == "FINANCIAL_CHART_OF_ACCOUNTS_CYCLE_DETECTED"

    async def test_delete_guards_active_children_and_in_use(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, _ = await _full_access_actor(client, tenants)
        supplier_id = await _create_supplier(client, headers)
        cost_center_id = await _create_cost_center(client, headers)

        root_id = await _create_chart_of_accounts(client, headers)
        child_id = await _create_chart_of_accounts(client, headers, parent_id=root_id)

        blocked_by_children = await client.delete(f"/api/v1/plano-contas/{root_id}", headers=headers)
        assert blocked_by_children.status_code == 409, blocked_by_children.text
        assert blocked_by_children.json()["error"]["code"] == "FINANCIAL_CHART_OF_ACCOUNTS_HAS_ACTIVE_CHILDREN"

        delete_child = await client.delete(f"/api/v1/plano-contas/{child_id}", headers=headers)
        assert delete_child.status_code == 204

        payable = await client.post(
            "/api/v1/contas-pagar", headers=headers,
            json={
                "supplier_id": supplier_id, "cost_center_id": cost_center_id, "origin": "AJUSTE_MANUAL",
                "value": "100.00", "due_date": "2026-09-01", "chart_of_accounts_id": root_id,
            },
        )
        assert payable.status_code == 201, payable.text

        blocked_in_use = await client.delete(f"/api/v1/plano-contas/{root_id}", headers=headers)
        assert blocked_in_use.status_code == 409, blocked_in_use.text
        assert blocked_in_use.json()["error"]["code"] == "FINANCIAL_CHART_OF_ACCOUNTS_IN_USE"


class TestBankAccountFlow:
    async def test_crud_and_saldo(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, _ = await _full_access_actor(client, tenants)

        bank_account_id = await _create_bank_account(client, headers)

        saldo = await client.get(f"/api/v1/contas-bancarias/{bank_account_id}/saldo", headers=headers)
        assert saldo.status_code == 200, saldo.text
        assert Decimal(saldo.json()["balance"]) == Decimal("0.00")

        patch_resp = await client.patch(
            f"/api/v1/contas-bancarias/{bank_account_id}", headers=headers, json={"branch": "0002"}
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["branch"] == "0002"
        assert patch_resp.json()["account_number"] is not None  # imutável, mas continua presente

        delete_resp = await client.delete(f"/api/v1/contas-bancarias/{bank_account_id}", headers=headers)
        assert delete_resp.status_code == 204

        after = await client.get(f"/api/v1/contas-bancarias/{bank_account_id}", headers=headers)
        assert after.status_code == 404


class TestAccountsPayableFlow:
    async def test_alcada_auto_routes_lancada_to_aprovada_when_under_threshold(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, _ = await _full_access_actor(client, tenants)
        supplier_id = await _create_supplier(client, headers)
        cost_center_id = await _create_cost_center(client, headers)
        chart_id = await _create_chart_of_accounts(client, headers)

        create = await client.post(
            "/api/v1/contas-pagar", headers=headers,
            json={
                "supplier_id": supplier_id, "cost_center_id": cost_center_id, "origin": "AJUSTE_MANUAL",
                "value": "500.00", "due_date": "2026-09-01", "chart_of_accounts_id": chart_id,
            },
        )
        assert create.status_code == 201, create.text
        assert create.json()["status"] == "APROVADA"  # abaixo da alçada, aprovação automática

    async def test_alcada_auto_routes_lancada_to_aguardando_aprovacao_above_threshold_then_approve_and_pay(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, _ = await _full_access_actor(client, tenants)
        supplier_id = await _create_supplier(client, headers)
        cost_center_id = await _create_cost_center(client, headers)
        chart_id = await _create_chart_of_accounts(client, headers)
        bank_account_id = await _create_bank_account(client, headers)

        create = await client.post(
            "/api/v1/contas-pagar", headers=headers,
            json={
                "supplier_id": supplier_id, "cost_center_id": cost_center_id, "origin": "AJUSTE_MANUAL",
                "value": str(ALCADA_PADRAO + Decimal("1")), "due_date": "2026-09-01", "chart_of_accounts_id": chart_id,
            },
        )
        assert create.status_code == 201, create.text
        payable_id = create.json()["id"]
        assert create.json()["status"] == "AGUARDANDO_APROVACAO"

        pay_too_early = await client.post(
            f"/api/v1/contas-pagar/{payable_id}/commands/pay", headers=headers, json={"bank_account_id": bank_account_id}
        )
        assert pay_too_early.status_code == 409
        assert pay_too_early.json()["error"]["code"] == "FINANCIAL_PAYABLE_INVALID_TRANSITION"

        approve = await client.post(f"/api/v1/contas-pagar/{payable_id}/commands/approve", headers=headers, json={})
        assert approve.status_code == 200, approve.text
        assert approve.json()["status"] == "APROVADA"

        pay = await client.post(
            f"/api/v1/contas-pagar/{payable_id}/commands/pay", headers=headers, json={"bank_account_id": bank_account_id}
        )
        assert pay.status_code == 200, pay.text
        assert pay.json()["status"] == "PAGA"

    async def test_reject_requires_justification(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, _ = await _full_access_actor(client, tenants)
        supplier_id = await _create_supplier(client, headers)
        cost_center_id = await _create_cost_center(client, headers)
        chart_id = await _create_chart_of_accounts(client, headers)

        create = await client.post(
            "/api/v1/contas-pagar", headers=headers,
            json={
                "supplier_id": supplier_id, "cost_center_id": cost_center_id, "origin": "AJUSTE_MANUAL",
                "value": str(ALCADA_PADRAO + Decimal("1")), "due_date": "2026-09-01", "chart_of_accounts_id": chart_id,
            },
        )
        payable_id = create.json()["id"]

        missing_justification = await client.post(
            f"/api/v1/contas-pagar/{payable_id}/commands/reject", headers=headers, json={}
        )
        assert missing_justification.status_code == 400
        assert missing_justification.json()["error"]["code"] == "FINANCIAL_PAYABLE_JUSTIFICATION_REQUIRED"

        reject = await client.post(
            f"/api/v1/contas-pagar/{payable_id}/commands/reject", headers=headers,
            json={"justification": "Fornecedor incorreto."},
        )
        assert reject.status_code == 200, reject.text
        assert reject.json()["status"] == "REJEITADA"

    async def test_pay_requires_active_bank_account(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, _ = await _full_access_actor(client, tenants)
        supplier_id = await _create_supplier(client, headers)
        cost_center_id = await _create_cost_center(client, headers)
        chart_id = await _create_chart_of_accounts(client, headers)
        bank_account_id = await _create_bank_account(client, headers)
        deactivate = await client.patch(
            f"/api/v1/contas-bancarias/{bank_account_id}", headers=headers, json={"status": "INATIVA"}
        )
        assert deactivate.status_code == 200

        create = await client.post(
            "/api/v1/contas-pagar", headers=headers,
            json={
                "supplier_id": supplier_id, "cost_center_id": cost_center_id, "origin": "AJUSTE_MANUAL",
                "value": "100.00", "due_date": "2026-09-01", "chart_of_accounts_id": chart_id,
            },
        )
        payable_id = create.json()["id"]

        pay = await client.post(
            f"/api/v1/contas-pagar/{payable_id}/commands/pay", headers=headers, json={"bank_account_id": bank_account_id}
        )
        assert pay.status_code == 400
        assert pay.json()["error"]["code"] == "FINANCIAL_BANK_ACCOUNT_INACTIVE"

    async def test_delete_only_allowed_in_lancada(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, _ = await _full_access_actor(client, tenants)
        supplier_id = await _create_supplier(client, headers)
        cost_center_id = await _create_cost_center(client, headers)
        chart_id = await _create_chart_of_accounts(client, headers)

        create = await client.post(
            "/api/v1/contas-pagar", headers=headers,
            json={
                "supplier_id": supplier_id, "cost_center_id": cost_center_id, "origin": "AJUSTE_MANUAL",
                "value": "100.00", "due_date": "2026-09-01", "chart_of_accounts_id": chart_id,
            },
        )
        payable_id = create.json()["id"]
        assert create.json()["status"] == "APROVADA"  # nunca LANCADA de forma observável (ver helper)

        blocked = await client.delete(f"/api/v1/contas-pagar/{payable_id}", headers=headers)
        assert blocked.status_code == 409
        assert blocked.json()["error"]["code"] == "FINANCIAL_PAYABLE_DELETE_INVALID_STATUS"


class TestInvoiceAndReceivableFlow:
    async def test_create_requires_pod_and_cte(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        payment_method_id = await _seed_payment_method(tenant_id)
        client_id = await _create_client_entity(client, headers)
        driver_id = await _create_driver(client, headers)
        vehicle_id = await _create_vehicle(client, headers, category_id)

        create_trip = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create_trip.json()["id"]
        await _allocate_and_plan(client, headers, trip_id, driver_id, vehicle_id)

        missing_precondition = await client.post(
            "/api/v1/faturas", headers=headers,
            json={
                "trip_id": trip_id, "client_id": client_id, "total_value": "1000.00",
                "payment_method_id": str(payment_method_id),
                "installments": [{"value": "1000.00", "due_date": "2026-10-01"}],
            },
        )
        assert missing_precondition.status_code == 409, missing_precondition.text
        assert missing_precondition.json()["error"]["code"] == "FINANCIAL_INVOICE_MISSING_PRECONDITION"

    async def test_full_invoice_lifecycle_and_confirm_receipt_advances_trip(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        payment_method_id = await _seed_payment_method(tenant_id)
        trip_id, _ = await _prepare_invoiceable_trip(client, headers, tenant_id, category_id)
        client_id_resp = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
        client_id = client_id_resp.json()["references"]["client_id"]

        create_invoice = await client.post(
            "/api/v1/faturas", headers=headers,
            json={
                "trip_id": trip_id, "client_id": client_id, "total_value": "1000.00",
                "payment_method_id": str(payment_method_id),
                "installments": [
                    {"value": "600.00", "due_date": "2026-10-01"}, {"value": "400.00", "due_date": "2026-11-01"},
                ],
            },
        )
        assert create_invoice.status_code == 201, create_invoice.text
        invoice_id = create_invoice.json()["id"]
        assert create_invoice.json()["status"] == "EMITIDA"

        trip_after_invoice = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
        assert trip_after_invoice.json()["status"]["financial"] == "FATURADA"

        receivables = await client.get(f"/api/v1/faturas/{invoice_id}/contas-receber", headers=headers)
        assert receivables.status_code == 200
        parcelas = sorted(receivables.json()["data"], key=lambda r: r["installment_number"])
        assert [p["value"] for p in parcelas] == ["600.00", "400.00"]

        extra_installment = await client.post(
            f"/api/v1/faturas/{invoice_id}/contas-receber", headers=headers,
            json={"value": "50.00", "due_date": "2026-12-01"},
        )
        assert extra_installment.status_code == 201, extra_installment.text
        assert extra_installment.json()["installment_number"] == 3

        first_confirm = await client.post(
            f"/api/v1/faturas/{invoice_id}/contas-receber/{parcelas[0]['id']}/commands/confirm-receipt",
            headers=headers, json={"received_value": "600.00"},
        )
        assert first_confirm.status_code == 200, first_confirm.text
        assert first_confirm.json()["status"] == "RECEBIDA"

        trip_mid = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
        assert trip_mid.json()["status"]["financial"] == "FATURADA"  # ainda há parcelas pendentes

        second_confirm = await client.post(
            f"/api/v1/faturas/{invoice_id}/contas-receber/{parcelas[1]['id']}/commands/confirm-receipt",
            headers=headers, json={"received_value": "400.00"},
        )
        assert second_confirm.status_code == 200, second_confirm.text

        third_confirm = await client.post(
            f"/api/v1/faturas/{invoice_id}/contas-receber/{extra_installment.json()['id']}/commands/confirm-receipt",
            headers=headers, json={"received_value": "50.00"},
        )
        assert third_confirm.status_code == 200, third_confirm.text

        trip_final = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
        assert trip_final.json()["status"]["financial"] == "RECEBIDA"  # última parcela confirmada

        cancel = await client.post(f"/api/v1/faturas/{invoice_id}/commands/cancel", headers=headers)
        assert cancel.status_code == 200, cancel.text
        assert cancel.json()["status"] == "CANCELADA"

        cancel_again = await client.post(f"/api/v1/faturas/{invoice_id}/commands/cancel", headers=headers)
        assert cancel_again.status_code == 409
        assert cancel_again.json()["error"]["code"] == "FINANCIAL_INVOICE_INVALID_STATUS"


class TestFinancialReversalFlow:
    async def test_target_mismatch_and_not_found(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, _ = await _full_access_actor(client, tenants)

        no_target = await client.post(
            "/api/v1/estornos-financeiros", headers=headers, json={"value": "10.00", "reason": "Teste"}
        )
        assert no_target.status_code == 400
        assert no_target.json()["error"]["code"] == "FINANCIAL_REVERSAL_TARGET_MISMATCH"

        two_targets = await client.post(
            "/api/v1/estornos-financeiros", headers=headers,
            json={
                "accounts_payable_id": str(uuid.uuid4()), "accounts_receivable_id": str(uuid.uuid4()),
                "value": "10.00", "reason": "Teste",
            },
        )
        assert two_targets.status_code == 400
        assert two_targets.json()["error"]["code"] == "FINANCIAL_REVERSAL_TARGET_MISMATCH"

        nonexistent_target = await client.post(
            "/api/v1/estornos-financeiros", headers=headers,
            json={"accounts_payable_id": str(uuid.uuid4()), "value": "10.00", "reason": "Teste"},
        )
        assert nonexistent_target.status_code == 404
        assert nonexistent_target.json()["error"]["code"] == "FINANCIAL_REVERSAL_TARGET_NOT_FOUND"


class TestTotalsDerivedFromAllocationAudit:
    """Auditoria #1 do usuário — `Trip.custo_realizado` é derivado por agregação dos Rateios de
    Despesa, nunca editável diretamente: criar/remover uma Conta a Pagar `origin=VIAGEM` recomputa o
    total; nenhum endpoint aceita o valor realizado como campo de entrada."""

    async def test_creating_and_removing_payable_recomputes_realized_cost(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        supplier_id = await _create_supplier(client, headers)
        cost_center_id = await _create_cost_center(client, headers)
        chart_id = await _create_chart_of_accounts(client, headers)

        client_id = await _create_client_entity(client, headers)
        create_trip = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create_trip.json()["id"]

        view_headers = {**headers}  # actor tem freight.trip.view + as 3 permissões financeiras (full access)

        baseline = await client.get(f"/api/v1/viagens/{trip_id}/financeiro", headers=view_headers)
        assert baseline.status_code == 200
        assert baseline.json()["actual_cost"] in (None, "0.00")

        first = await client.post(
            "/api/v1/contas-pagar", headers=headers,
            json={
                "supplier_id": supplier_id, "cost_center_id": cost_center_id, "origin": "VIAGEM", "trip_id": trip_id,
                "value": "300.00", "due_date": "2026-09-01", "chart_of_accounts_id": chart_id,
            },
        )
        assert first.status_code == 201, first.text
        first_id = first.json()["id"]

        after_first = await client.get(f"/api/v1/viagens/{trip_id}/financeiro", headers=view_headers)
        assert after_first.json()["actual_cost"] == "300.00"

        second = await client.post(
            "/api/v1/contas-pagar", headers=headers,
            json={
                "supplier_id": supplier_id, "cost_center_id": cost_center_id, "origin": "VIAGEM", "trip_id": trip_id,
                "value": "200.00", "due_date": "2026-09-01", "chart_of_accounts_id": chart_id,
            },
        )
        assert second.status_code == 201, second.text

        after_second = await client.get(f"/api/v1/viagens/{trip_id}/financeiro", headers=view_headers)
        assert after_second.json()["actual_cost"] == "500.00"  # soma dos dois rateios, nunca substituição

        # "remover item" — DELETE só é alcançável em LANCADA (ver `_force_payable_status`); o
        # endpoint real é exercitado normalmente a partir daí.
        await _force_payable_status(first_id, "LANCADA")
        delete_resp = await client.delete(f"/api/v1/contas-pagar/{first_id}", headers=headers)
        assert delete_resp.status_code == 204, delete_resp.text

        after_delete = await client.get(f"/api/v1/viagens/{trip_id}/financeiro", headers=view_headers)
        assert after_delete.json()["actual_cost"] == "200.00"  # só o segundo rateio permanece

    async def test_no_endpoint_accepts_realized_cost_directly(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, _ = await _full_access_actor(client, tenants)
        client_id = await _create_client_entity(client, headers)
        create_trip = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
        trip_id = create_trip.json()["id"]

        # `UpdateTripRequest`/`CreateAccountsPayableRequest`/etc. não têm nenhum campo
        # `actual_cost`/`custo_realizado` — um valor "estranho" no corpo é ignorado
        # silenciosamente (`extra=\"ignore\"`), nunca aplicado.
        rogue_patch = await client.patch(
            f"/api/v1/viagens/{trip_id}", headers=headers, json={"actual_cost": "999999.00", "custo_realizado": "999999.00"}
        )
        assert rogue_patch.status_code == 200

        financeiro = await client.get(f"/api/v1/viagens/{trip_id}/financeiro", headers=headers)
        assert financeiro.json()["actual_cost"] in (None, "0.00")


class TestStatusHistoryAudit:
    """Auditoria #2 do usuário — toda mudança relevante de status gera exatamente um registro em
    `contas_pagar_status_history`/`contas_receber_status_history`, sem transições silenciosas
    (incluindo a derivada `LANCADA→AGUARDANDO_APROVACAO/APROVADA`, que também grava sua própria
    linha no momento da criação)."""

    async def _history_count(self, model: Any, column_name: str, entity_id: str) -> int:
        session_factory = get_session_factory()
        async with session_factory() as session:
            column = getattr(model, column_name)
            rows = (await session.execute(select(model.id).where(column == uuid.UUID(entity_id)))).all()
        return len(rows)

    async def test_every_payable_transition_produces_exactly_one_history_row(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, _ = await _full_access_actor(client, tenants)
        supplier_id = await _create_supplier(client, headers)
        cost_center_id = await _create_cost_center(client, headers)
        chart_id = await _create_chart_of_accounts(client, headers)
        bank_account_id = await _create_bank_account(client, headers)

        create = await client.post(
            "/api/v1/contas-pagar", headers=headers,
            json={
                "supplier_id": supplier_id, "cost_center_id": cost_center_id, "origin": "AJUSTE_MANUAL",
                "value": str(ALCADA_PADRAO + Decimal("1")), "due_date": "2026-09-01", "chart_of_accounts_id": chart_id,
            },
        )
        payable_id = create.json()["id"]
        assert create.json()["status"] == "AGUARDANDO_APROVACAO"

        count_after_create = await self._history_count(PayableStatusHistoryModel, "conta_pagar_id", payable_id)
        assert count_after_create == 1  # a derivação LANCADA→AGUARDANDO_APROVACAO já gera sua linha

        approve = await client.post(f"/api/v1/contas-pagar/{payable_id}/commands/approve", headers=headers, json={})
        assert approve.status_code == 200

        count_after_approve = await self._history_count(PayableStatusHistoryModel, "conta_pagar_id", payable_id)
        assert count_after_approve == 2

        pay = await client.post(
            f"/api/v1/contas-pagar/{payable_id}/commands/pay", headers=headers, json={"bank_account_id": bank_account_id}
        )
        assert pay.status_code == 200

        count_after_pay = await self._history_count(PayableStatusHistoryModel, "conta_pagar_id", payable_id)
        assert count_after_pay == 3  # nenhuma transição real ficou sem sua própria linha

    async def test_every_receivable_transition_produces_exactly_one_history_row(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        payment_method_id = await _seed_payment_method(tenant_id)
        trip_id, _ = await _prepare_invoiceable_trip(client, headers, tenant_id, category_id)
        client_id_resp = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
        client_id = client_id_resp.json()["references"]["client_id"]

        create_invoice = await client.post(
            "/api/v1/faturas", headers=headers,
            json={
                "trip_id": trip_id, "client_id": client_id, "total_value": "100.00",
                "payment_method_id": str(payment_method_id), "installments": [{"value": "100.00", "due_date": "2026-10-01"}],
            },
        )
        invoice_id = create_invoice.json()["id"]
        receivables = await client.get(f"/api/v1/faturas/{invoice_id}/contas-receber", headers=headers)
        receivable_id = receivables.json()["data"][0]["id"]

        count_after_create = await self._history_count(ReceivableStatusHistoryModel, "conta_receber_id", receivable_id)
        assert count_after_create == 1  # PENDENTE, gravado na criação

        confirm = await client.post(
            f"/api/v1/faturas/{invoice_id}/contas-receber/{receivable_id}/commands/confirm-receipt",
            headers=headers, json={"received_value": "100.00"},
        )
        assert confirm.status_code == 200

        count_after_confirm = await self._history_count(ReceivableStatusHistoryModel, "conta_receber_id", receivable_id)
        assert count_after_confirm == 2


class TestEstornoNeverRevertsAudit:
    """Auditoria #3 do usuário (D266/D273) — um Estorno nunca "volta" o estado anterior: o
    lançamento original continua historicamente no seu status real (`PAGA`), e o Estorno existe como
    sua própria trilha paralela, nunca como uma nova linha em `contas_pagar_status_history`."""

    async def test_reversal_against_paid_payable_never_changes_its_status(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers, _, _ = await _full_access_actor(client, tenants)
        supplier_id = await _create_supplier(client, headers)
        cost_center_id = await _create_cost_center(client, headers)
        chart_id = await _create_chart_of_accounts(client, headers)
        bank_account_id = await _create_bank_account(client, headers)

        create = await client.post(
            "/api/v1/contas-pagar", headers=headers,
            json={
                "supplier_id": supplier_id, "cost_center_id": cost_center_id, "origin": "AJUSTE_MANUAL",
                "value": "300.00", "due_date": "2026-09-01", "chart_of_accounts_id": chart_id,
            },
        )
        payable_id = create.json()["id"]
        assert create.json()["status"] == "APROVADA"  # abaixo da alçada

        pay = await client.post(
            f"/api/v1/contas-pagar/{payable_id}/commands/pay", headers=headers, json={"bank_account_id": bank_account_id}
        )
        assert pay.status_code == 200
        assert pay.json()["status"] == "PAGA"

        session_factory = get_session_factory()
        async with session_factory() as session:
            history_before = (
                await session.execute(
                    select(PayableStatusHistoryModel.id).where(
                        PayableStatusHistoryModel.conta_pagar_id == uuid.UUID(payable_id)
                    )
                )
            ).all()

        reversal = await client.post(
            "/api/v1/estornos-financeiros", headers=headers,
            json={"accounts_payable_id": payable_id, "value": "300.00", "reason": "Pagamento em duplicidade."},
        )
        assert reversal.status_code == 201, reversal.text

        still_paid = await client.get(f"/api/v1/contas-pagar/{payable_id}", headers=headers)
        assert still_paid.json()["status"] == "PAGA"  # nunca reverte

        async with session_factory() as session:
            history_after = (
                await session.execute(
                    select(PayableStatusHistoryModel.id).where(
                        PayableStatusHistoryModel.conta_pagar_id == uuid.UUID(payable_id)
                    )
                )
            ).all()
        assert len(history_after) == len(history_before)  # Estorno não grava linha no histórico do alvo

        reversals_for_payable = await client.get(
            "/api/v1/estornos-financeiros", headers=headers, params={"accounts_payable_id": payable_id}
        )
        assert reversals_for_payable.status_code == 200
        assert reversals_for_payable.json()["meta"]["pagination"]["total"] == 1  # sua própria trilha, isolada


class TestTripFinancialsFieldLevelRbacAudit:
    """Auditoria #4 do usuário (D267-style) — `GET /viagens/{id}/financeiro` mascara cada grupo de
    campos conforme a permissão do ator: sem `financial.trip_predicted_value.view`/`.trip_actual_
    value.view`/`.trip_margin.view`, os campos correspondentes voltam `null`; sem nenhuma das três
    (mesmo com `freight.trip.view`), `403`."""

    async def _prepare_trip_with_all_value_groups(
        self, client: AsyncClient, headers: dict[str, str], tenant_id: uuid.UUID, category_id: uuid.UUID
    ) -> str:
        supplier_id = await _create_supplier(client, headers)
        cost_center_id = await _create_cost_center(client, headers)
        chart_id = await _create_chart_of_accounts(client, headers)
        payment_method_id = await _seed_payment_method(tenant_id)

        trip_id, _ = await _prepare_invoiceable_trip(client, headers, tenant_id, category_id)

        # Valores previstos não nascem de nenhum comando neste lote (Cotação/Programação da
        # Viagem, fora de escopo — `038-financial-trip.md`) — setados direto para o teste poder
        # provar a máscara com dado real, não com "null por ausência de dado".
        session_factory = get_session_factory()
        async with session_factory() as session:
            await session.execute(
                text(
                    "UPDATE viagens SET receita_prevista_snapshot = :receita, custo_previsto = :custo WHERE id = :id"
                ),
                {"receita": "1000.00", "custo": "600.00", "id": trip_id},
            )
            await session.commit()

        payable = await client.post(
            "/api/v1/contas-pagar", headers=headers,
            json={
                "supplier_id": supplier_id, "cost_center_id": cost_center_id, "origin": "VIAGEM", "trip_id": trip_id,
                "value": "400.00", "due_date": "2026-09-01", "chart_of_accounts_id": chart_id,
            },
        )
        assert payable.status_code == 201, payable.text

        client_id_resp = await client.get(f"/api/v1/viagens/{trip_id}", headers=headers)
        client_id = client_id_resp.json()["references"]["client_id"]
        invoice = await client.post(
            "/api/v1/faturas", headers=headers,
            json={
                "trip_id": trip_id, "client_id": client_id, "total_value": "1000.00",
                "payment_method_id": str(payment_method_id), "installments": [{"value": "1000.00", "due_date": "2026-10-01"}],
            },
        )
        assert invoice.status_code == 201, invoice.text
        receivables = await client.get(f"/api/v1/faturas/{invoice.json()['id']}/contas-receber", headers=headers)
        receivable_id = receivables.json()["data"][0]["id"]
        confirm = await client.post(
            f"/api/v1/faturas/{invoice.json()['id']}/contas-receber/{receivable_id}/commands/confirm-receipt",
            headers=headers, json={"received_value": "1000.00"},
        )
        assert confirm.status_code == 200, confirm.text

        return trip_id

    async def test_field_groups_are_masked_per_permission(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        full_headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        trip_id = await self._prepare_trip_with_all_value_groups(client, full_headers, tenant_id, category_id)

        full_view = await client.get(f"/api/v1/viagens/{trip_id}/financeiro", headers=full_headers)
        assert full_view.status_code == 200, full_view.text
        body = full_view.json()
        assert body["predicted_revenue"] == "1000.00"
        assert body["predicted_cost"] == "600.00"
        assert body["predicted_margin"] == "400.00"
        assert body["actual_cost"] == "400.00"
        assert body["actual_revenue"] == "1000.00"
        assert body["actual_margin"] == "600.00"
        assert body["financial_status"] == "RECEBIDA"

        role_predicted = await _create_role(
            tenant_id, ["freight.trip.view", "financial.trip_predicted_value.view"]
        )
        _, email_predicted = await _create_user(tenant_id, role_ids=frozenset({role_predicted}))
        predicted_headers = await _login(client, email_predicted)

        predicted_view = await client.get(f"/api/v1/viagens/{trip_id}/financeiro", headers=predicted_headers)
        assert predicted_view.status_code == 200, predicted_view.text
        predicted_body = predicted_view.json()
        assert predicted_body["predicted_revenue"] == "1000.00"
        assert predicted_body["predicted_cost"] == "600.00"
        assert predicted_body["predicted_margin"] == "400.00"
        assert predicted_body["actual_cost"] is None
        assert predicted_body["actual_revenue"] is None
        assert predicted_body["actual_margin"] is None
        assert predicted_body["financial_deviation"] is None

        role_none = await _create_role(tenant_id, ["freight.trip.view"])
        _, email_none = await _create_user(tenant_id, role_ids=frozenset({role_none}))
        none_headers = await _login(client, email_none)

        no_value_permission = await client.get(f"/api/v1/viagens/{trip_id}/financeiro", headers=none_headers)
        assert no_value_permission.status_code == 403
        assert no_value_permission.json()["error"]["code"] == "IDENTITY_PERMISSION_DENIED"

        role_value_no_trip_view = await _create_role(tenant_id, ["financial.trip_actual_value.view"])
        _, email_no_trip_view = await _create_user(tenant_id, role_ids=frozenset({role_value_no_trip_view}))
        no_trip_view_headers = await _login(client, email_no_trip_view)

        without_trip_view = await client.get(f"/api/v1/viagens/{trip_id}/financeiro", headers=no_trip_view_headers)
        assert without_trip_view.status_code == 403


class TestTenantIsolation:
    async def test_cross_tenant_access_returns_404_or_403(
        self, client: AsyncClient, permission_ids: dict[str, uuid.UUID], tenants: list[uuid.UUID]
    ) -> None:
        headers_a, _, _ = await _full_access_actor(client, tenants)
        headers_b, _, _ = await _full_access_actor(client, tenants)

        chart_id_b = await _create_chart_of_accounts(client, headers_b)

        cross_tenant = await client.get(f"/api/v1/plano-contas/{chart_id_b}", headers=headers_a)
        assert cross_tenant.status_code == 404
        assert cross_tenant.json()["error"]["code"] == "FINANCIAL_CHART_OF_ACCOUNTS_NOT_FOUND"
