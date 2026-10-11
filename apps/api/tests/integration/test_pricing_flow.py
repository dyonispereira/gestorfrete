from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from core.database.session import get_session_factory
from core.multitenancy.context import reset_current_tenant_id, set_current_tenant_id
from modules.freight.application.trip_internal_transitions import TripInternalTransitions
from modules.freight.infrastructure.persistence.models.trip_price_application_model import (
    TripPriceApplicationModel,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)
from modules.pricing.infrastructure.persistence.models.price_table_model import (
    PriceTableItemModel,
    PriceTableModel,
)

from tests.integration.test_fiscal_flow import (  # noqa: E402
    _cleanup_tenant,
    _create_client_entity,
    _create_driver,
    _create_role,
    _create_tenant,
    _create_user,
    _create_vehicle,
    _login,
    _seed_vehicle_category,
)

pytestmark = pytest.mark.integration
"""Lote 2 (`GESTORFRETE — PROMPT MESTRE`) — Tabela de Frete: CRUD completo, cálculo determinístico
por unidade, snapshot de aplicação numa Viagem, dados de carga/percurso, isolamento tenant, RBAC,
idempotência e concorrência."""


_PRICING_PERMISSIONS = [
    "pricing.price_table.view", "pricing.price_table.create", "pricing.price_table.edit",
    "freight.trip.view", "freight.trip.edit", "freight.trip.create", "freight.trip.dispatch",
    "crm.client.create", "drivers.driver.create", "fleet.vehicle.create", "fleet.vehicle_category.create",
    "documents.cte.view",
]


async def _cleanup_pricing_tenant(tenant_id: uuid.UUID) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        await session.execute(
            delete(TripPriceApplicationModel).where(TripPriceApplicationModel.tenant_id == tenant_id)
        )
        await session.execute(delete(PriceTableItemModel).where(PriceTableItemModel.tenant_id == tenant_id))
        await session.execute(delete(PriceTableModel).where(PriceTableModel.tenant_id == tenant_id))
        await session.commit()
    await _cleanup_tenant(tenant_id)


@pytest.fixture
async def tenants() -> AsyncIterator[list[uuid.UUID]]:
    created: list[uuid.UUID] = []
    yield created
    for tenant_id in created:
        await _cleanup_pricing_tenant(tenant_id)


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


async def _full_pricing_actor(
    client: AsyncClient, tenants: list[uuid.UUID]
) -> tuple[dict[str, str], uuid.UUID, uuid.UUID]:
    """Retorna (headers, tenant_id, category_id)."""

    tenant_id = await _create_tenant()
    tenants.append(tenant_id)
    category_id = await _seed_vehicle_category(tenant_id)
    role_id = await _create_role(tenant_id, _PRICING_PERMISSIONS)
    _, email = await _create_user(tenant_id, role_ids=frozenset({role_id}))
    headers = await _login(client, email)
    return headers, tenant_id, category_id


def _valid_table_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "nome": f"Tabela {uuid.uuid4().hex[:6]}", "direcao": "VENDA",
        "vigencia_inicio": date.today().isoformat(),
    }
    payload.update(overrides)
    return payload


async def _create_table(client: AsyncClient, headers: dict[str, str], **overrides: Any) -> dict[str, Any]:
    resp = await client.post("/api/v1/tabelas-preco", headers=headers, json=_valid_table_payload(**overrides))
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _create_item(
    client: AsyncClient, headers: dict[str, str], table_id: str, **overrides: Any
) -> dict[str, Any]:
    payload: dict[str, Any] = {"unidade_calculo": "VIAGEM", "valor": "1500.00"}
    payload.update(overrides)
    resp = await client.post(f"/api/v1/tabelas-preco/{table_id}/itens", headers=headers, json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _activate_table(client: AsyncClient, headers: dict[str, str], table_id: str) -> dict[str, Any]:
    resp = await client.post(f"/api/v1/tabelas-preco/{table_id}/commands/activate", headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _create_trip_not_dispatched(
    client: AsyncClient, headers: dict[str, str], category_id: uuid.UUID
) -> str:
    client_id = await _create_client_entity(client, headers)
    driver_id = await _create_driver(client, headers)
    vehicle_id = await _create_vehicle(client, headers, category_id)

    create = await client.post("/api/v1/viagens", headers=headers, json={"cliente_id": client_id})
    assert create.status_code == 201, create.text
    trip_id: str = create.json()["id"]

    allocation = await client.post(
        f"/api/v1/viagens/{trip_id}/resources", headers=headers,
        json={"driver_id": driver_id, "tractor_unit_id": vehicle_id},
    )
    assert allocation.status_code == 201, allocation.text
    return trip_id


class TestPriceTableCrud:
    async def test_cria_tabela_venda_e_compra(self, client: AsyncClient, tenants: list[uuid.UUID]) -> None:
        headers, _, _ = await _full_pricing_actor(client, tenants)

        venda = await _create_table(client, headers, direcao="VENDA")
        assert venda["direcao"] == "VENDA"
        assert venda["status"] == "RASCUNHO"
        assert venda["versao"] == 1

        compra = await _create_table(client, headers, direcao="COMPRA")
        assert compra["direcao"] == "COMPRA"

    async def test_cliente_id_rejeitado_para_compra(self, client: AsyncClient, tenants: list[uuid.UUID]) -> None:
        headers, _, _ = await _full_pricing_actor(client, tenants)
        resp = await client.post(
            "/api/v1/tabelas-preco", headers=headers,
            json=_valid_table_payload(direcao="COMPRA", cliente_id=str(uuid.uuid4())),
        )
        assert resp.status_code == 400, resp.text

    async def test_ativar_sem_item_e_rejeitado(self, client: AsyncClient, tenants: list[uuid.UUID]) -> None:
        headers, _, _ = await _full_pricing_actor(client, tenants)
        table = await _create_table(client, headers)
        resp = await client.post(f"/api/v1/tabelas-preco/{table['id']}/commands/activate", headers=headers)
        assert resp.status_code == 400, resp.text

    async def test_ativar_incrementa_versao_e_bloqueia_novo_item(
        self, client: AsyncClient, tenants: list[uuid.UUID]
    ) -> None:
        headers, _, _ = await _full_pricing_actor(client, tenants)
        table = await _create_table(client, headers)
        await _create_item(client, headers, table["id"])

        activated = await _activate_table(client, headers, table["id"])
        assert activated["status"] == "VIGENTE"
        assert activated["versao"] == 2

        resp = await client.post(
            f"/api/v1/tabelas-preco/{table['id']}/itens", headers=headers,
            json={"unidade_calculo": "VIAGEM", "valor": "999.00"},
        )
        assert resp.status_code == 409, resp.text

    async def test_expirar_tabela(self, client: AsyncClient, tenants: list[uuid.UUID]) -> None:
        headers, _, _ = await _full_pricing_actor(client, tenants)
        table = await _create_table(client, headers)
        await _create_item(client, headers, table["id"])
        await _activate_table(client, headers, table["id"])

        resp = await client.post(f"/api/v1/tabelas-preco/{table['id']}/commands/expire", headers=headers)
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "EXPIRADA"

    async def test_item_faixa_distancia_exige_min_max_e_modo(
        self, client: AsyncClient, tenants: list[uuid.UUID]
    ) -> None:
        headers, _, _ = await _full_pricing_actor(client, tenants)
        table = await _create_table(client, headers)
        resp = await client.post(
            f"/api/v1/tabelas-preco/{table['id']}/itens", headers=headers,
            json={"unidade_calculo": "FAIXA_DISTANCIA", "valor": "10.00"},
        )
        assert resp.status_code == 400, resp.text

    async def test_item_percentual_exige_base_descricao(
        self, client: AsyncClient, tenants: list[uuid.UUID]
    ) -> None:
        headers, _, _ = await _full_pricing_actor(client, tenants)
        table = await _create_table(client, headers)
        resp = await client.post(
            f"/api/v1/tabelas-preco/{table['id']}/itens", headers=headers,
            json={"unidade_calculo": "PERCENTUAL", "valor": "5.00"},
        )
        assert resp.status_code == 400, resp.text

    async def test_isolamento_entre_tenants(self, client: AsyncClient, tenants: list[uuid.UUID]) -> None:
        headers_a, _, _ = await _full_pricing_actor(client, tenants)
        headers_b, _, _ = await _full_pricing_actor(client, tenants)
        table = await _create_table(client, headers_a)

        resp = await client.get(f"/api/v1/tabelas-preco/{table['id']}", headers=headers_b)
        assert resp.status_code == 404, resp.text

    async def test_rbac_sem_permissao_create(self, client: AsyncClient, tenants: list[uuid.UUID]) -> None:
        tenant_id = await _create_tenant()
        tenants.append(tenant_id)
        role_id = await _create_role(tenant_id, ["pricing.price_table.view"])
        _, email = await _create_user(tenant_id, role_ids=frozenset({role_id}))
        headers = await _login(client, email)

        resp = await client.post("/api/v1/tabelas-preco", headers=headers, json=_valid_table_payload())
        assert resp.status_code == 403, resp.text


class TestTripCargoRoute:
    async def test_atualiza_dados_de_carga_e_percurso(
        self, client: AsyncClient, tenants: list[uuid.UUID]
    ) -> None:
        headers, _, category_id = await _full_pricing_actor(client, tenants)
        trip_id = await _create_trip_not_dispatched(client, headers, category_id)

        resp = await client.patch(
            f"/api/v1/viagens/{trip_id}", headers=headers,
            json={
                "origem_cidade": "São Paulo", "origem_uf": "SP", "destino_cidade": "Curitiba",
                "destino_uf": "PR", "distancia_prevista_km": "408.50", "peso_carga_kg": "12500.00",
                "tipo_carga": "Grãos", "quantidade_carga": 500, "unidade_quantidade_carga": "SACA",
            },
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()["cargo_route"]
        assert body["origin_city"] == "São Paulo"
        assert body["origin_state"] == "SP"
        assert body["destination_state"] == "PR"
        assert Decimal(body["predicted_distance_km"]) == Decimal("408.50")
        assert Decimal(body["cargo_weight_kg"]) == Decimal("12500.00")
        # 12500 kg / 1000 = 12.5 toneladas — coluna GENERATED, nunca calculada em Python.
        assert Decimal(body["cargo_weight_tons"]) == Decimal("12.500")

    async def test_distancia_zero_e_rejeitada(self, client: AsyncClient, tenants: list[uuid.UUID]) -> None:
        headers, _, category_id = await _full_pricing_actor(client, tenants)
        trip_id = await _create_trip_not_dispatched(client, headers, category_id)
        resp = await client.patch(
            f"/api/v1/viagens/{trip_id}", headers=headers, json={"distancia_prevista_km": "0"}
        )
        assert resp.status_code == 422, resp.text


class TestApplyPriceTable:
    async def test_unidade_viagem(self, client: AsyncClient, tenants: list[uuid.UUID]) -> None:
        headers, _, category_id = await _full_pricing_actor(client, tenants)
        trip_id = await _create_trip_not_dispatched(client, headers, category_id)

        table = await _create_table(client, headers)
        item = await _create_item(client, headers, table["id"], unidade_calculo="VIAGEM", valor="2000.00")
        await _activate_table(client, headers, table["id"])

        resp = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/apply-price-table", headers=headers,
            json={"price_table_item_id": item["id"]},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert Decimal(body["snapshots"]["predicted_revenue_snapshot"]) == Decimal("2000.00")
        assert body["snapshots"]["applied_price_table_id"] == table["id"]
        assert body["snapshots"]["applied_price_table_application_id"] is not None

    async def test_unidade_km(self, client: AsyncClient, tenants: list[uuid.UUID]) -> None:
        headers, _, category_id = await _full_pricing_actor(client, tenants)
        trip_id = await _create_trip_not_dispatched(client, headers, category_id)
        await client.patch(
            f"/api/v1/viagens/{trip_id}", headers=headers, json={"distancia_prevista_km": "100.00"}
        )

        table = await _create_table(client, headers)
        item = await _create_item(client, headers, table["id"], unidade_calculo="KM", valor="10.00")
        await _activate_table(client, headers, table["id"])

        resp = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/apply-price-table", headers=headers,
            json={"price_table_item_id": item["id"]},
        )
        assert resp.status_code == 200, resp.text
        assert Decimal(resp.json()["snapshots"]["predicted_revenue_snapshot"]) == Decimal("1000.00")

    async def test_unidade_km_sem_distancia_e_rejeitado(
        self, client: AsyncClient, tenants: list[uuid.UUID]
    ) -> None:
        headers, _, category_id = await _full_pricing_actor(client, tenants)
        trip_id = await _create_trip_not_dispatched(client, headers, category_id)

        table = await _create_table(client, headers)
        item = await _create_item(client, headers, table["id"], unidade_calculo="KM", valor="10.00")
        await _activate_table(client, headers, table["id"])

        resp = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/apply-price-table", headers=headers,
            json={"price_table_item_id": item["id"]},
        )
        assert resp.status_code == 400, resp.text

    async def test_unidade_tonelada_e_kg(self, client: AsyncClient, tenants: list[uuid.UUID]) -> None:
        headers, _, category_id = await _full_pricing_actor(client, tenants)
        trip_id = await _create_trip_not_dispatched(client, headers, category_id)
        await client.patch(f"/api/v1/viagens/{trip_id}", headers=headers, json={"peso_carga_kg": "5000.00"})

        table = await _create_table(client, headers)
        item_ton = await _create_item(client, headers, table["id"], unidade_calculo="TONELADA", valor="100.00")
        await _activate_table(client, headers, table["id"])

        resp = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/apply-price-table", headers=headers,
            json={"price_table_item_id": item_ton["id"]},
        )
        assert resp.status_code == 200, resp.text
        # 5000kg = 5 toneladas × 100 = 500.00
        assert Decimal(resp.json()["snapshots"]["predicted_revenue_snapshot"]) == Decimal("500.00")

    async def test_unidade_kg(self, client: AsyncClient, tenants: list[uuid.UUID]) -> None:
        headers, _, category_id = await _full_pricing_actor(client, tenants)
        trip_id = await _create_trip_not_dispatched(client, headers, category_id)
        await client.patch(f"/api/v1/viagens/{trip_id}", headers=headers, json={"peso_carga_kg": "250.00"})

        table = await _create_table(client, headers)
        item_kg = await _create_item(client, headers, table["id"], unidade_calculo="KG", valor="2.00")
        await _activate_table(client, headers, table["id"])

        resp = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/apply-price-table", headers=headers,
            json={"price_table_item_id": item_kg["id"]},
        )
        assert resp.status_code == 200, resp.text
        assert Decimal(resp.json()["snapshots"]["predicted_revenue_snapshot"]) == Decimal("500.00")

    async def test_faixa_distancia_tarifa_por_km_dentro_da_faixa(
        self, client: AsyncClient, tenants: list[uuid.UUID]
    ) -> None:
        headers, _, category_id = await _full_pricing_actor(client, tenants)
        trip_id = await _create_trip_not_dispatched(client, headers, category_id)
        await client.patch(
            f"/api/v1/viagens/{trip_id}", headers=headers, json={"distancia_prevista_km": "150.00"}
        )

        table = await _create_table(client, headers)
        item = await _create_item(
            client, headers, table["id"], unidade_calculo="FAIXA_DISTANCIA", valor="5.00",
            faixa_distancia_min_km="100.00", faixa_distancia_max_km="200.00", faixa_modo="TARIFA_POR_KM",
        )
        await _activate_table(client, headers, table["id"])

        resp = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/apply-price-table", headers=headers,
            json={"price_table_item_id": item["id"]},
        )
        assert resp.status_code == 200, resp.text
        assert Decimal(resp.json()["snapshots"]["predicted_revenue_snapshot"]) == Decimal("750.00")

    async def test_faixa_distancia_valor_fixo(self, client: AsyncClient, tenants: list[uuid.UUID]) -> None:
        headers, _, category_id = await _full_pricing_actor(client, tenants)
        trip_id = await _create_trip_not_dispatched(client, headers, category_id)
        await client.patch(
            f"/api/v1/viagens/{trip_id}", headers=headers, json={"distancia_prevista_km": "150.00"}
        )

        table = await _create_table(client, headers)
        item = await _create_item(
            client, headers, table["id"], unidade_calculo="FAIXA_DISTANCIA", valor="900.00",
            faixa_distancia_min_km="100.00", faixa_distancia_max_km="200.00", faixa_modo="VALOR_FIXO",
        )
        await _activate_table(client, headers, table["id"])

        resp = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/apply-price-table", headers=headers,
            json={"price_table_item_id": item["id"]},
        )
        assert resp.status_code == 200, resp.text
        assert Decimal(resp.json()["snapshots"]["predicted_revenue_snapshot"]) == Decimal("900.00")

    async def test_faixa_distancia_fora_do_range_e_rejeitada(
        self, client: AsyncClient, tenants: list[uuid.UUID]
    ) -> None:
        headers, _, category_id = await _full_pricing_actor(client, tenants)
        trip_id = await _create_trip_not_dispatched(client, headers, category_id)
        await client.patch(
            f"/api/v1/viagens/{trip_id}", headers=headers, json={"distancia_prevista_km": "999.00"}
        )

        table = await _create_table(client, headers)
        item = await _create_item(
            client, headers, table["id"], unidade_calculo="FAIXA_DISTANCIA", valor="5.00",
            faixa_distancia_min_km="100.00", faixa_distancia_max_km="200.00", faixa_modo="TARIFA_POR_KM",
        )
        await _activate_table(client, headers, table["id"])

        resp = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/apply-price-table", headers=headers,
            json={"price_table_item_id": item["id"]},
        )
        assert resp.status_code == 400, resp.text

    async def test_percentual_exige_base_no_comando(self, client: AsyncClient, tenants: list[uuid.UUID]) -> None:
        headers, _, category_id = await _full_pricing_actor(client, tenants)
        trip_id = await _create_trip_not_dispatched(client, headers, category_id)

        table = await _create_table(client, headers)
        item = await _create_item(
            client, headers, table["id"], unidade_calculo="PERCENTUAL", valor="10.00",
            base_percentual_descricao="Valor do contrato guarda-chuva #123",
        )
        await _activate_table(client, headers, table["id"])

        # Sem base_percentual_valor no comando — rejeitado, nunca inventa a partir de outro campo.
        resp = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/apply-price-table", headers=headers,
            json={"price_table_item_id": item["id"]},
        )
        assert resp.status_code == 400, resp.text

        resp2 = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/apply-price-table", headers=headers,
            json={"price_table_item_id": item["id"], "base_percentual_valor": "5000.00"},
        )
        assert resp2.status_code == 200, resp2.text
        assert Decimal(resp2.json()["snapshots"]["predicted_revenue_snapshot"]) == Decimal("500.00")

    async def test_adicionais_descontos_ordem_deterministica(
        self, client: AsyncClient, tenants: list[uuid.UUID]
    ) -> None:
        headers, _, category_id = await _full_pricing_actor(client, tenants)
        trip_id = await _create_trip_not_dispatched(client, headers, category_id)

        table = await _create_table(client, headers)
        # base 1000 + adicional_fixo 100 = 1100; - desconto_fixo 50 = 1050;
        # × (1 + 10/100) = 1155; × (1 - 5/100) = 1097.25
        item = await _create_item(
            client, headers, table["id"], unidade_calculo="VIAGEM", valor="1000.00",
            adicional_fixo="100.00", desconto_fixo="50.00", adicional_percentual="10.00",
            desconto_percentual="5.00",
        )
        await _activate_table(client, headers, table["id"])

        resp = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/apply-price-table", headers=headers,
            json={"price_table_item_id": item["id"]},
        )
        assert resp.status_code == 200, resp.text
        assert Decimal(resp.json()["snapshots"]["predicted_revenue_snapshot"]) == Decimal("1097.25")

    async def test_valor_minimo_prevalece(self, client: AsyncClient, tenants: list[uuid.UUID]) -> None:
        headers, _, category_id = await _full_pricing_actor(client, tenants)
        trip_id = await _create_trip_not_dispatched(client, headers, category_id)

        table = await _create_table(client, headers)
        item = await _create_item(
            client, headers, table["id"], unidade_calculo="VIAGEM", valor="100.00", valor_minimo="1500.00"
        )
        await _activate_table(client, headers, table["id"])

        resp = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/apply-price-table", headers=headers,
            json={"price_table_item_id": item["id"]},
        )
        assert resp.status_code == 200, resp.text
        assert Decimal(resp.json()["snapshots"]["predicted_revenue_snapshot"]) == Decimal("1500.00")

    async def test_reaplicar_sem_remover_e_rejeitado(
        self, client: AsyncClient, tenants: list[uuid.UUID]
    ) -> None:
        headers, _, category_id = await _full_pricing_actor(client, tenants)
        trip_id = await _create_trip_not_dispatched(client, headers, category_id)

        table = await _create_table(client, headers)
        item = await _create_item(client, headers, table["id"])
        await _activate_table(client, headers, table["id"])

        first = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/apply-price-table", headers=headers,
            json={"price_table_item_id": item["id"]},
        )
        assert first.status_code == 200, first.text

        second = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/apply-price-table", headers=headers,
            json={"price_table_item_id": item["id"]},
        )
        assert second.status_code == 409, second.text

    async def test_remover_aplicacao_limpa_snapshot(
        self, client: AsyncClient, tenants: list[uuid.UUID]
    ) -> None:
        headers, _, category_id = await _full_pricing_actor(client, tenants)
        trip_id = await _create_trip_not_dispatched(client, headers, category_id)

        table = await _create_table(client, headers)
        item = await _create_item(client, headers, table["id"])
        await _activate_table(client, headers, table["id"])

        await client.post(
            f"/api/v1/viagens/{trip_id}/commands/apply-price-table", headers=headers,
            json={"price_table_item_id": item["id"]},
        )

        resp = await client.delete(
            f"/api/v1/viagens/{trip_id}/commands/apply-price-table", headers=headers
        )
        assert resp.status_code == 200, resp.text
        snapshots = resp.json()["snapshots"]
        assert snapshots["predicted_revenue_snapshot"] is None
        assert snapshots["applied_price_table_id"] is None
        assert snapshots["applied_price_table_application_id"] is None

        # Reaplicar depois de remover funciona normalmente.
        reapply = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/apply-price-table", headers=headers,
            json={"price_table_item_id": item["id"]},
        )
        assert reapply.status_code == 200, reapply.text

    async def test_aplicacao_removida_nunca_e_apagada_fisicamente(
        self, client: AsyncClient, tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_pricing_actor(client, tenants)
        trip_id = await _create_trip_not_dispatched(client, headers, category_id)

        table = await _create_table(client, headers)
        item = await _create_item(client, headers, table["id"])
        await _activate_table(client, headers, table["id"])

        await client.post(
            f"/api/v1/viagens/{trip_id}/commands/apply-price-table", headers=headers,
            json={"price_table_item_id": item["id"]},
        )
        await client.delete(f"/api/v1/viagens/{trip_id}/commands/apply-price-table", headers=headers)

        session_factory = get_session_factory()
        async with session_factory() as session:
            rows = (
                await session.execute(
                    select(TripPriceApplicationModel).where(TripPriceApplicationModel.viagem_id == uuid.UUID(trip_id))
                )
            ).scalars().all()
        assert len(rows) == 1
        assert rows[0].removido_em is not None

    async def test_compra_bloqueada_sem_transportador(
        self, client: AsyncClient, tenants: list[uuid.UUID]
    ) -> None:
        headers, _, category_id = await _full_pricing_actor(client, tenants)
        trip_id = await _create_trip_not_dispatched(client, headers, category_id)

        table = await _create_table(client, headers, direcao="COMPRA")
        item = await _create_item(client, headers, table["id"])
        await _activate_table(client, headers, table["id"])

        resp = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/apply-price-table", headers=headers,
            json={"price_table_item_id": item["id"]},
        )
        assert resp.status_code == 409, resp.text
        assert resp.json()["error"]["code"] == "PRICING_PURCHASE_APPLICATION_REQUIRES_CARRIER"

    async def test_remocao_bloqueada_apos_cte_emitido(
        self, client: AsyncClient, tenants: list[uuid.UUID]
    ) -> None:
        headers, tenant_id, category_id = await _full_pricing_actor(client, tenants)
        trip_id = await _create_trip_not_dispatched(client, headers, category_id)

        table = await _create_table(client, headers)
        item = await _create_item(client, headers, table["id"])
        await _activate_table(client, headers, table["id"])
        await client.post(
            f"/api/v1/viagens/{trip_id}/commands/apply-price-table", headers=headers,
            json={"price_table_item_id": item["id"]},
        )

        # Precisa de FiscalConfig para despachar de verdade — sem ela, dispatch falha antes de
        # emitir CT-e e o teste não provaria nada. Seed direto (mesmo padrão de
        # `_seed_fiscal_configuration`, test_fiscal_flow.py) só para alcançar o estado necessário.
        from modules.documents.infrastructure.persistence.models.fiscal_configuration_model import (
            FiscalConfigurationModel,
        )

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

        simulator = TripInternalTransitions()
        now = datetime.now(timezone.utc)
        token = set_current_tenant_id(tenant_id)
        try:
            await simulator.await_checklist(trip_id=uuid.UUID(trip_id), now=now)
            await simulator.approve_checklist(trip_id=uuid.UUID(trip_id), now=now)
        finally:
            reset_current_tenant_id(token)

        dispatch = await client.post(f"/api/v1/viagens/{trip_id}/commands/dispatch", headers=headers)
        assert dispatch.status_code == 200, dispatch.text

        remove = await client.delete(
            f"/api/v1/viagens/{trip_id}/commands/apply-price-table", headers=headers
        )
        assert remove.status_code == 409, remove.text
        assert remove.json()["error"]["code"] == "FREIGHT_TRIP_PRICE_REMOVAL_BLOCKED_BY_FISCAL"

    async def test_idempotencia_mesma_key_mesmo_efeito(
        self, client: AsyncClient, tenants: list[uuid.UUID]
    ) -> None:
        headers, _, category_id = await _full_pricing_actor(client, tenants)
        trip_id = await _create_trip_not_dispatched(client, headers, category_id)

        table = await _create_table(client, headers)
        item = await _create_item(client, headers, table["id"])
        await _activate_table(client, headers, table["id"])

        key = str(uuid.uuid4())
        first = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/apply-price-table", headers={**headers, "Idempotency-Key": key},
            json={"price_table_item_id": item["id"]},
        )
        assert first.status_code == 200, first.text

        second = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/apply-price-table", headers={**headers, "Idempotency-Key": key},
            json={"price_table_item_id": item["id"]},
        )
        assert second.status_code == 200, second.text
        assert first.json() == second.json()

        session_factory = get_session_factory()
        async with session_factory() as session:
            rows = (
                await session.execute(
                    select(TripPriceApplicationModel).where(TripPriceApplicationModel.viagem_id == uuid.UUID(trip_id))
                )
            ).scalars().all()
        assert len(rows) == 1

    async def test_concorrencia_apenas_uma_aplicacao_vence(
        self, client: AsyncClient, tenants: list[uuid.UUID]
    ) -> None:
        """Mesmo padrão determinístico do Hotfix P0 (Fase 2): duas requisições concorrentes de
        apply-price-table na MESMA Viagem — o lock pessimista (`get_by_id_for_update`) serializa,
        a segunda relê o estado já atualizado e corretamente rejeita com
        `FREIGHT_TRIP_PRICE_ALREADY_APPLIED` — nunca 2 aplicações simultâneas."""

        headers, _, category_id = await _full_pricing_actor(client, tenants)
        trip_id = await _create_trip_not_dispatched(client, headers, category_id)

        table = await _create_table(client, headers)
        item = await _create_item(client, headers, table["id"])
        await _activate_table(client, headers, table["id"])

        original = SqlAlchemyTripRepository.get_by_id_for_update
        first_read_started = asyncio.Event()
        both_can_proceed = asyncio.Event()
        state = {"count": 0}

        async def instrumented(self_repo: SqlAlchemyTripRepository, id: uuid.UUID) -> object:
            state["count"] += 1
            n = state["count"]
            if n == 1:
                first_read_started.set()
                await both_can_proceed.wait()
            elif n == 2:
                await first_read_started.wait()
                both_can_proceed.set()
            return await original(self_repo, id)

        with patch.object(SqlAlchemyTripRepository, "get_by_id_for_update", instrumented):
            responses = await asyncio.gather(
                client.post(
                    f"/api/v1/viagens/{trip_id}/commands/apply-price-table", headers=headers,
                    json={"price_table_item_id": item["id"]},
                ),
                client.post(
                    f"/api/v1/viagens/{trip_id}/commands/apply-price-table", headers=headers,
                    json={"price_table_item_id": item["id"]},
                ),
            )

        statuses = sorted(r.status_code for r in responses)
        assert statuses == [200, 409], f"esperava [200, 409], obteve {statuses}"

        session_factory = get_session_factory()
        async with session_factory() as session:
            rows = (
                await session.execute(
                    select(TripPriceApplicationModel).where(
                        TripPriceApplicationModel.viagem_id == uuid.UUID(trip_id),
                        TripPriceApplicationModel.removido_em.is_(None),
                    )
                )
            ).scalars().all()
        assert len(rows) == 1
