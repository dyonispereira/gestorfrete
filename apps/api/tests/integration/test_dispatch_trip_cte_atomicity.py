from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from core.database.session import get_session_factory
from core.multitenancy.context import reset_current_tenant_id, set_current_tenant_id
from modules.documents.infrastructure.persistence.models.cte_model import CteModel
from modules.documents.infrastructure.persistence.models.fiscal_configuration_model import (
    FiscalConfigurationModel,
)
from modules.fleet.infrastructure.persistence.models.odometer_reading_model import OdometerReadingModel
from modules.freight.infrastructure.persistence.models.trip_model import TripModel
from modules.freight.application.trip_internal_transitions import TripInternalTransitions
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_trip_repository import (
    SqlAlchemyTripRepository,
)

# Reaproveita os helpers de domínio já validados em test_fiscal_flow.py (mesma infra, mesmo
# padrão de tenant/role/user/client/driver/vehicle) — só as fixtures pytest (client/tenants/
# permission_ids) são declaradas localmente abaixo, para não colidir com o parâmetro de mesmo
# nome em cada teste (ruff F811 — nome de fixture importado vs. nome de parâmetro é o padrão
# normal do pytest, mas o linter não distingue os dois casos).
from tests.integration.test_fiscal_flow import (
    ALL_PERMISSION_CODES,
    _cleanup_tenant,
    _create_and_dispatch_trip,
    _create_client_entity,
    _create_driver,
    _create_role,
    _create_tenant,
    _create_user,
    _create_vehicle,
    _full_access_actor,
    _login,
    _seed_permissions,
    _seed_vehicle_category,
)

pytestmark = pytest.mark.integration
"""Hotfix P0 (Gate 6, incidente `VG-2026-6574BB`) — DispatchTrip×CT-e deixaram de ser duas
transações separadas. Prova, contra Postgres real, que: (1) `FiscalConfig` ausente falha ANTES de
qualquer mutação da Viagem; (2) sucesso é atômico (Viagem+CT-e+contador fiscal, um commit só); (3)
falha durante a criação do CT-e reverte a Viagem inteira, nenhum efeito parcial sobrevive; (4)
idempotência/concorrência continuam corretas com o novo desenho."""


async def _create_trip_ready_to_dispatch(
    client: AsyncClient, headers: dict[str, str], tenant_id: uuid.UUID, category_id: uuid.UUID
) -> str:
    """Mesma sequência de `_create_and_dispatch_trip`, mas para logo ANTES do dispatch — para os
    testes que querem controlar o próprio momento/resultado do `commands/dispatch`."""

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

    simulator = TripInternalTransitions()
    now = datetime.now(timezone.utc)
    token = set_current_tenant_id(tenant_id)
    try:
        await simulator.await_checklist(trip_id=uuid.UUID(trip_id), now=now)
        await simulator.approve_checklist(trip_id=uuid.UUID(trip_id), now=now)
    finally:
        reset_current_tenant_id(token)

    return trip_id


async def _trip_status(tenant_id: uuid.UUID, trip_id: str) -> str:
    session_factory = get_session_factory()
    async with session_factory() as session:
        row = (
            await session.execute(select(TripModel.status_operacional).where(TripModel.id == uuid.UUID(trip_id)))
        ).scalar_one()
        return str(row)


async def _cte_count_for_trip(tenant_id: uuid.UUID, trip_id: str) -> int:
    session_factory = get_session_factory()
    async with session_factory() as session:
        rows = (
            await session.execute(select(CteModel.id).where(CteModel.viagem_id == uuid.UUID(trip_id)))
        ).scalars().all()
        return len(rows)


@pytest.fixture
async def permission_ids() -> dict[str, uuid.UUID]:
    return await _seed_permissions()


@pytest.fixture
async def tenants() -> AsyncIterator[list[uuid.UUID]]:
    created: list[uuid.UUID] = []
    yield created
    for tenant_id in created:
        # `_cleanup_tenant` (test_fiscal_flow.py) nunca precisou limpar `leituras_hodometro` —
        # nenhum teste de lá passa `departure_odometer_km` no dispatch. Os testes de concorrência/
        # rollback deste arquivo passam, então limpamos aqui antes, para não quebrar a FK ao
        # apagar `veiculos_tracionadores`.
        session_factory = get_session_factory()
        async with session_factory() as session:
            await session.execute(delete(OdometerReadingModel).where(OdometerReadingModel.tenant_id == tenant_id))
            await session.commit()
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


async def _proximo_numero_cte(tenant_id: uuid.UUID) -> int:
    session_factory = get_session_factory()
    async with session_factory() as session:
        row = (
            await session.execute(
                select(FiscalConfigurationModel.proximo_numero_cte).where(
                    FiscalConfigurationModel.tenant_id == tenant_id
                )
            )
        ).scalar_one()
        return int(row)


async def _dispatch_concurrently_synced(
    client: AsyncClient, trip_id: str, headers_a: dict[str, str], headers_b: dict[str, str]
) -> list[int]:
    """Força duas requisições de dispatch a lerem a Viagem ANTES de qualquer uma commitar —
    reprodução determinística da corrida real que o CI encontrou (Hotfix P0 Fase 2), não
    dependente de timing de rede/scheduler. Sincroniza no ponto exato onde a corrida acontece
    (`SqlAlchemyTripRepository.get_by_id_for_update`, chamado no início do `DispatchTripHandler`):
    a 1ª chamada espera a 2ª também ter entrado na leitura antes de qualquer uma prosseguir —
    depois disso, a execução real decide (com o lock pessimista, só uma consegue avançar por vez,
    e a segunda relê o estado já atualizado ao ser liberada)."""

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
            client.post(f"/api/v1/viagens/{trip_id}/commands/dispatch", headers=headers_a),
            client.post(f"/api/v1/viagens/{trip_id}/commands/dispatch", headers=headers_b),
        )
    return [r.status_code for r in responses]


class TestDispatchTripCteAtomicity:
    async def test_fiscal_config_ausente_falha_antes_de_qualquer_mutacao(
        self, client: AsyncClient, tenants: list[uuid.UUID], permission_ids: dict[str, uuid.UUID]
    ) -> None:
        """(1) FiscalConfig ausente → dispatch falha e viagem permanece LIBERADA. (2) CT-e não é
        criado. Cobre também: "o pré-requisito deve ser validado antes de qualquer mutação"."""

        tenant_id = await _create_tenant()
        tenants.append(tenant_id)
        category_id = await _seed_vehicle_category(tenant_id)
        # Deliberadamente SEM _seed_fiscal_configuration — é o pré-requisito ausente sob teste.
        role_id = await _create_role(tenant_id, ALL_PERMISSION_CODES)
        _, email = await _create_user(tenant_id, role_ids=frozenset({role_id}))
        headers = await _login(client, email)

        trip_id = await _create_trip_ready_to_dispatch(client, headers, tenant_id, category_id)
        assert await _trip_status(tenant_id, trip_id) == "LIBERADA"

        dispatch = await client.post(f"/api/v1/viagens/{trip_id}/commands/dispatch", headers=headers)

        assert dispatch.status_code == 404, dispatch.text
        assert dispatch.json()["error"]["code"] == "FISCAL_CONFIG_NOT_FOUND"
        assert await _trip_status(tenant_id, trip_id) == "LIBERADA"
        assert await _cte_count_for_trip(tenant_id, trip_id) == 0

    async def test_fiscal_config_valida_despacho_completo_um_cte(
        self, client: AsyncClient, tenants: list[uuid.UUID], permission_ids: dict[str, uuid.UUID]
    ) -> None:
        """(3) FiscalConfig válida → dispatch funciona. (4) viagem chega em EM_DESLOCAMENTO. (5)
        exatamente um CT-e é criado."""

        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        trip_id = await _create_and_dispatch_trip(client, headers, tenant_id, category_id)

        assert await _trip_status(tenant_id, trip_id) == "EM_DESLOCAMENTO"
        assert await _cte_count_for_trip(tenant_id, trip_id) == 1

    async def test_retry_mesma_idempotency_key_nao_duplica_efeitos(
        self, client: AsyncClient, tenants: list[uuid.UUID], permission_ids: dict[str, uuid.UUID]
    ) -> None:
        """(6) retry com a mesma Idempotency-Key não duplica efeitos — replay coerente."""

        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        trip_id = await _create_trip_ready_to_dispatch(client, headers, tenant_id, category_id)
        idem_headers = {**headers, "Idempotency-Key": f"gate6-hotfix-{uuid.uuid4()}"}

        first = await client.post(f"/api/v1/viagens/{trip_id}/commands/dispatch", headers=idem_headers)
        second = await client.post(f"/api/v1/viagens/{trip_id}/commands/dispatch", headers=idem_headers)

        assert first.status_code == 200, first.text
        assert second.status_code == 200, second.text
        assert first.json() == second.json()
        assert await _trip_status(tenant_id, trip_id) == "EM_DESLOCAMENTO"
        assert await _cte_count_for_trip(tenant_id, trip_id) == 1

    async def test_mesma_key_payload_diferente_mantem_conflito(
        self, client: AsyncClient, tenants: list[uuid.UUID], permission_ids: dict[str, uuid.UUID]
    ) -> None:
        """(7) mesma Idempotency-Key + payload diferente → conflito esperado (não duplica CT-e)."""

        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        trip_id = await _create_trip_ready_to_dispatch(client, headers, tenant_id, category_id)
        key = f"gate6-hotfix-{uuid.uuid4()}"

        first = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/dispatch", headers={**headers, "Idempotency-Key": key},
            json={"departure_odometer_km": "1000.0"},
        )
        second = await client.post(
            f"/api/v1/viagens/{trip_id}/commands/dispatch", headers={**headers, "Idempotency-Key": key},
            json={"departure_odometer_km": "999999.0"},
        )

        assert first.status_code == 200, first.text
        assert second.status_code == 409, second.text
        assert second.json()["error"]["code"] == "IDEMPOTENCY_KEY_PAYLOAD_MISMATCH"
        assert await _cte_count_for_trip(tenant_id, trip_id) == 1

    async def test_concorrencia_keys_diferentes_apenas_uma_transicao_valida(
        self, client: AsyncClient, tenants: list[uuid.UUID], permission_ids: dict[str, uuid.UUID]
    ) -> None:
        """(8) Hotfix P0 Fase 2 — duas requisições simultâneas com Idempotency-Keys DIFERENTES
        (cenário real plausível: portal do gestor e app do motorista despachando a mesma Viagem
        quase ao mesmo tempo). Reprodução determinística, não dependente de timing de rede — antes
        da Fase 2 isto reproduzia [200, 200] e 2 CT-es de forma 100% confiável."""

        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        trip_id = await _create_trip_ready_to_dispatch(client, headers, tenant_id, category_id)
        numero_antes = await _proximo_numero_cte(tenant_id)

        headers_a = {**headers, "Idempotency-Key": f"conc-a-{uuid.uuid4()}"}
        headers_b = {**headers, "Idempotency-Key": f"conc-b-{uuid.uuid4()}"}
        statuses = await _dispatch_concurrently_synced(client, trip_id, headers_a, headers_b)

        assert sorted(statuses) == [200, 409], f"esperava [200, 409], obteve {statuses}"
        assert await _cte_count_for_trip(tenant_id, trip_id) == 1
        assert await _proximo_numero_cte(tenant_id) == numero_antes + 1
        assert await _trip_status(tenant_id, trip_id) == "EM_DESLOCAMENTO"

    async def test_concorrencia_sem_idempotency_key_apenas_uma_transicao_valida(
        self, client: AsyncClient, tenants: list[uuid.UUID], permission_ids: dict[str, uuid.UUID]
    ) -> None:
        """(8) mesma corrida, mas sem NENHUMA Idempotency-Key — o endpoint aceita a requisição sem
        key (`with_idempotency` pula toda a lógica de idempotência nesse caso), então a única
        proteção real contra duplicação é o lock pessimista da Fase 2, não a camada de
        idempotência. Antes da correção, reproduzia [200, 200] + 2 CT-es igual ao cenário com keys
        diferentes — idempotência e controle de concorrência são garantias distintas."""

        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        trip_id = await _create_trip_ready_to_dispatch(client, headers, tenant_id, category_id)
        numero_antes = await _proximo_numero_cte(tenant_id)

        statuses = await _dispatch_concurrently_synced(client, trip_id, headers, headers)

        assert sorted(statuses) == [200, 409], f"esperava [200, 409], obteve {statuses}"
        assert await _cte_count_for_trip(tenant_id, trip_id) == 1
        assert await _proximo_numero_cte(tenant_id) == numero_antes + 1
        assert await _trip_status(tenant_id, trip_id) == "EM_DESLOCAMENTO"

    async def test_falha_durante_criacao_do_cte_reverte_viagem_e_contador(
        self, client: AsyncClient, tenants: list[uuid.UUID], permission_ids: dict[str, uuid.UUID]
    ) -> None:
        """(9) exceção injetada DEPOIS de `trip.dispatch()`, durante a criação do CT-e, não deixa
        a Viagem parcialmente despachada — rollback integral. Também comprova explicitamente que
        `proximo_numero_cte` permanece inalterado quando a transação falha."""

        headers, tenant_id, category_id = await _full_access_actor(client, tenants)
        trip_id = await _create_trip_ready_to_dispatch(client, headers, tenant_id, category_id)
        numero_antes = await _proximo_numero_cte(tenant_id)

        # `RequestContextMiddleware` estende `BaseHTTPMiddleware` (Starlette) — uma exceção sem
        # handler registrado que atravessa esse tipo de middleware propaga como exceção Python
        # real através do `ASGITransport`/`TestClient`, não como uma `Response` 500 comum. Isso é
        # um comportamento conhecido de teste, não do servidor real (Uvicorn) em produção; o que
        # importa provar aqui é o estado do banco depois, não o transporte da exceção em si.
        with patch(
            "modules.documents.application.commands.create_cte.Cte.create",
            side_effect=RuntimeError("falha injetada — Gate 6 hotfix P0, teste de rollback integral"),
        ), pytest.raises(Exception, match="falha injetada"):
            await client.post(f"/api/v1/viagens/{trip_id}/commands/dispatch", headers=headers)

        assert await _trip_status(tenant_id, trip_id) == "LIBERADA"
        assert await _cte_count_for_trip(tenant_id, trip_id) == 0
        assert await _proximo_numero_cte(tenant_id) == numero_antes

        # Prova que a Viagem não ficou presa: um dispatch de verdade, depois da falha simulada,
        # continua funcionando normalmente (mesma prova de recuperação usada em VG-2026-6574BB).
        retry = await client.post(f"/api/v1/viagens/{trip_id}/commands/dispatch", headers=headers)
        assert retry.status_code == 200, retry.text
        assert await _trip_status(tenant_id, trip_id) == "EM_DESLOCAMENTO"
        assert await _cte_count_for_trip(tenant_id, trip_id) == 1
