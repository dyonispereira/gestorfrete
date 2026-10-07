from __future__ import annotations

import asyncio
import sys
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, update

from core.audit.models import LogAuditoriaModel
from core.database.session import get_session_factory
from core.exceptions.base import ConflictError, NotFoundError, ValidationError
from core.multitenancy.context import reset_current_tenant_id, set_current_tenant_id
from core.security.password_hasher import BcryptPasswordHasher
from modules.identity_access.application.commands.deactivate_user import (
    DeactivateUserCommand,
    DeactivateUserHandler,
)
from modules.identity_access.infrastructure.persistence.models.identity_models import (
    SessionModel,
    UserModel,
)
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from shared_kernel.domain.actor import AuthenticatedActor

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.reset_user_password import (  # noqa: E402
    MIN_PASSWORD_LENGTH,
    discover_tenant_candidates,
    reset_password,
)

from tests.integration.test_fiscal_flow import (  # noqa: E402
    PASSWORD,
    _cleanup_tenant,
    _create_tenant,
    _create_user,
    _login,
)

pytestmark = pytest.mark.integration
"""GAP IDENTITY Fase 1 (Gate 6) — CLI operacional `scripts/reset_user_password.py`. Resolve GAP A
(credencial perdida de usuário/tenant já existentes), nunca GAP B (bootstrap de primeiro admin,
backlog separado). Chama `reset_password()` diretamente (o núcleo testável, sem I/O de terminal),
nunca via subprocess — mesma UoW/Postgres real do resto da suíte de integração."""


NEW_PASSWORD = "Nova-Senha-Forte-456"


async def _user_hash(user_id: uuid.UUID) -> str:
    session_factory = get_session_factory()
    async with session_factory() as session:
        return (
            await session.execute(select(UserModel.senha_hash).where(UserModel.id == user_id))
        ).scalar_one()


async def _session_statuses(user_id: uuid.UUID) -> list[str]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        rows = (
            await session.execute(select(SessionModel.status).where(SessionModel.usuario_id == user_id))
        ).scalars().all()
        return list(rows)


async def _reset_audit_count(tenant_id: uuid.UUID, user_id: uuid.UUID) -> int:
    """Conta só as linhas de auditoria do PRÓPRIO reset (`acao="ALTERACAO"`) — `_create_user`
    (CRIACAO) e `_deactivate_user` (EXCLUSAO_LOGICA) já gravam suas próprias linhas para o mesmo
    `entidade_id`/`entidade_tipo`, que não devem contar aqui."""

    session_factory = get_session_factory()
    async with session_factory() as session:
        rows = (
            await session.execute(
                select(LogAuditoriaModel.id).where(
                    LogAuditoriaModel.tenant_id == tenant_id,
                    LogAuditoriaModel.entidade_id == user_id,
                    LogAuditoriaModel.entidade_tipo == "usuarios",
                    LogAuditoriaModel.acao == "ALTERACAO",
                )
            )
        ).scalars().all()
        return len(rows)


async def _set_user_status(user_id: uuid.UUID, status: str) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        await session.execute(update(UserModel).where(UserModel.id == user_id).values(status=status))
        await session.commit()


async def _deactivate_user(tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
    bootstrap_actor = AuthenticatedActor(user_id=uuid.uuid4(), tenant_id=tenant_id, session_id=uuid.uuid4())
    token = set_current_tenant_id(tenant_id)
    try:
        await DeactivateUserHandler().handle(DeactivateUserCommand(actor=bootstrap_actor, user_id=user_id))
    finally:
        reset_current_tenant_id(token)


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


class TestResetUserPasswordHappyPath:
    async def test_usuario_ativo_reset_funciona_sessao_antiga_revogada(
        self, client: AsyncClient, tenants: list[uuid.UUID]
    ) -> None:
        tenant_id = await _create_tenant()
        tenants.append(tenant_id)
        user_id, email = await _create_user(tenant_id, role_ids=frozenset())
        old_headers = await _login(client, email)

        old_token_check = await client.get("/api/v1/auth/me", headers=old_headers)
        assert old_token_check.status_code == 200

        await reset_password(tenant_id=tenant_id, email=email, new_password=NEW_PASSWORD)

        # A sessão emitida ANTES do reset já está encerrada imediatamente após o reset — antes de
        # qualquer novo login acontecer.
        assert await _session_statuses(user_id) == ["ENCERRADA"]
        assert await _reset_audit_count(tenant_id, user_id) == 1

        # Senha antiga não autentica mais.
        old_login = await client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
        assert old_login.status_code == 401, old_login.text

        # Senha nova autentica normalmente.
        new_login = await client.post("/api/v1/auth/login", json={"email": email, "password": NEW_PASSWORD})
        assert new_login.status_code == 200, new_login.text

        # A sessão/token emitido ANTES do reset deixa de ser aceito (revogação real, não só o
        # refresh token) — mesmo mecanismo de validação por request que o resto da API usa.
        rejected = await client.get("/api/v1/auth/me", headers=old_headers)
        assert rejected.status_code == 401, rejected.text


class TestResetUserPasswordCleanFailures:
    async def test_usuario_inexistente_nao_muda_nada(self, tenants: list[uuid.UUID]) -> None:
        tenant_id = await _create_tenant()
        tenants.append(tenant_id)

        with pytest.raises(NotFoundError) as exc_info:
            await reset_password(
                tenant_id=tenant_id, email="nao-existe@teste.com", new_password=NEW_PASSWORD
            )
        assert exc_info.value.code == "IDENTITY_USER_NOT_FOUND"

    async def test_tenant_inexistente_nao_muda_nada(self) -> None:
        with pytest.raises(NotFoundError) as exc_info:
            await reset_password(tenant_id=uuid.uuid4(), email="qualquer@teste.com", new_password=NEW_PASSWORD)
        assert exc_info.value.code == "TENANCY_TENANT_NOT_FOUND"

    async def test_tenant_incorreto_nao_afeta_usuario_de_outro_tenant(
        self, tenants: list[uuid.UUID]
    ) -> None:
        tenant_a = await _create_tenant()
        tenants.append(tenant_a)
        tenant_b = await _create_tenant()
        tenants.append(tenant_b)
        user_id, email = await _create_user(tenant_a, role_ids=frozenset())
        hash_before = await _user_hash(user_id)

        with pytest.raises(NotFoundError):
            await reset_password(tenant_id=tenant_b, email=email, new_password=NEW_PASSWORD)

        assert await _user_hash(user_id) == hash_before
        assert await _reset_audit_count(tenant_a, user_id) == 0

    async def test_usuario_inativo_reset_recusado(self, tenants: list[uuid.UUID]) -> None:
        tenant_id = await _create_tenant()
        tenants.append(tenant_id)
        user_id, email = await _create_user(tenant_id, role_ids=frozenset())
        await _deactivate_user(tenant_id, user_id)
        hash_before = await _user_hash(user_id)

        with pytest.raises(ConflictError) as exc_info:
            await reset_password(tenant_id=tenant_id, email=email, new_password=NEW_PASSWORD)
        assert exc_info.value.code == "IDENTITY_USER_NOT_RESETTABLE"
        assert await _user_hash(user_id) == hash_before
        assert await _reset_audit_count(tenant_id, user_id) == 0

    async def test_usuario_bloqueado_reset_recusado(self, tenants: list[uuid.UUID]) -> None:
        tenant_id = await _create_tenant()
        tenants.append(tenant_id)
        user_id, email = await _create_user(tenant_id, role_ids=frozenset())
        await _set_user_status(user_id, "BLOQUEADO")
        hash_before = await _user_hash(user_id)

        with pytest.raises(ConflictError) as exc_info:
            await reset_password(tenant_id=tenant_id, email=email, new_password=NEW_PASSWORD)
        assert exc_info.value.code == "IDENTITY_USER_NOT_RESETTABLE"
        assert await _user_hash(user_id) == hash_before

    async def test_senha_curta_recusada_antes_da_mutacao(self, tenants: list[uuid.UUID]) -> None:
        tenant_id = await _create_tenant()
        tenants.append(tenant_id)
        user_id, email = await _create_user(tenant_id, role_ids=frozenset())
        hash_before = await _user_hash(user_id)

        with pytest.raises(ValidationError) as exc_info:
            await reset_password(tenant_id=tenant_id, email=email, new_password="a" * (MIN_PASSWORD_LENGTH - 1))
        assert exc_info.value.code == "IDENTITY_PASSWORD_TOO_SHORT"
        assert await _user_hash(user_id) == hash_before
        assert await _reset_audit_count(tenant_id, user_id) == 0


class TestResetUserPasswordIsolationAndIntegrity:
    async def test_mesmo_email_tenants_diferentes_apenas_usuario_do_tenant_informado_afetado(
        self, tenants: list[uuid.UUID]
    ) -> None:
        """Achado da investigação: e-mail só é único POR tenant (`uq_usuarios_tenant_id_email`),
        não globalmente — o CLI precisa isolar corretamente mesmo nesse cenário (diferente do
        `get_by_email` do login, que busca globalmente e é o GAP separado registrado à parte)."""

        tenant_a = await _create_tenant()
        tenants.append(tenant_a)
        tenant_b = await _create_tenant()
        tenants.append(tenant_b)

        shared_email = f"compartilhado-{uuid.uuid4().hex[:8]}@teste.com"
        user_a_id = await _create_user_with_email(tenant_a, shared_email)
        user_b_id = await _create_user_with_email(tenant_b, shared_email)
        hash_a_before = await _user_hash(user_a_id)
        hash_b_before = await _user_hash(user_b_id)

        await reset_password(tenant_id=tenant_a, email=shared_email, new_password=NEW_PASSWORD)

        assert await _user_hash(user_a_id) != hash_a_before
        assert BcryptPasswordHasher().verify(NEW_PASSWORD, await _user_hash(user_a_id))
        assert await _user_hash(user_b_id) == hash_b_before
        assert await _reset_audit_count(tenant_b, user_b_id) == 0
        assert await _reset_audit_count(tenant_a, user_a_id) == 1

    async def test_nenhuma_senha_hash_token_em_auditoria(self, tenants: list[uuid.UUID]) -> None:
        tenant_id = await _create_tenant()
        tenants.append(tenant_id)
        user_id, email = await _create_user(tenant_id, role_ids=frozenset())

        await reset_password(tenant_id=tenant_id, email=email, new_password=NEW_PASSWORD)

        session_factory = get_session_factory()
        async with session_factory() as session:
            row = (
                await session.execute(
                    select(LogAuditoriaModel).where(
                        LogAuditoriaModel.entidade_id == user_id,
                        LogAuditoriaModel.tenant_id == tenant_id,
                        LogAuditoriaModel.acao == "ALTERACAO",
                    )
                )
            ).scalar_one()

        serialized = str(row.dados_antes) + str(row.dados_depois) + str(row.motivo) + str(row.ator_nome_snapshot)
        assert NEW_PASSWORD not in serialized
        assert PASSWORD not in serialized
        hasher = BcryptPasswordHasher()
        final_hash = await _user_hash(user_id)
        assert final_hash not in serialized
        assert row.ator_id is None
        assert row.origem == "SISTEMA"
        assert hasher.verify(NEW_PASSWORD, final_hash)

    async def test_falha_antes_do_commit_reverte_tudo(self, tenants: list[uuid.UUID]) -> None:
        """Injeta falha depois de `end_all_active_for_user` (sessão já "encerrada" em memória) mas
        antes do `commit()` — prova que a UoW reverte TUDO (hash, sessão, auditoria), não deixa
        nenhum efeito parcial, igual ao padrão já provado no Hotfix P0 para dispatch/CT-e."""

        tenant_id = await _create_tenant()
        tenants.append(tenant_id)
        user_id, email = await _create_user(tenant_id, role_ids=frozenset())
        hash_before = await _user_hash(user_id)

        from core.audit.audit_logger import AuditLogger

        async def _boom(self: AuditLogger, *args: object, **kwargs: object) -> None:
            raise RuntimeError("falha injetada antes do commit")

        with patch.object(AuditLogger, "record", _boom):
            with pytest.raises(RuntimeError):
                await reset_password(tenant_id=tenant_id, email=email, new_password=NEW_PASSWORD)

        assert await _user_hash(user_id) == hash_before
        assert await _session_statuses(user_id) in ([], ["ATIVA"])
        assert await _reset_audit_count(tenant_id, user_id) == 0


class TestResetUserPasswordConcurrency:
    async def test_concorrencia_mesmo_usuario_resultado_consistente(
        self, tenants: list[uuid.UUID]
    ) -> None:
        """Reprodução determinística via `FOR UPDATE` (mesmo padrão do Hotfix P0 Fase 2): duas
        chamadas concorrentes de `reset_password` para o mesmo usuário não devem deadlockar nem
        corromper estado — o lock pessimista em `get_by_email_in_tenant_for_update` serializa as
        duas transações; o resultado final é consistente (senha final autentica, exatamente duas
        linhas de auditoria, sem exceção)."""

        tenant_id = await _create_tenant()
        tenants.append(tenant_id)
        user_id, email = await _create_user(tenant_id, role_ids=frozenset())

        original = SqlAlchemyUserRepository.get_by_email_in_tenant_for_update
        first_read_started = asyncio.Event()
        both_can_proceed = asyncio.Event()
        state = {"count": 0}

        async def instrumented(self_repo: SqlAlchemyUserRepository, email_arg: str) -> object:
            state["count"] += 1
            n = state["count"]
            if n == 1:
                first_read_started.set()
                await both_can_proceed.wait()
            elif n == 2:
                await first_read_started.wait()
                both_can_proceed.set()
            return await original(self_repo, email_arg)

        with patch.object(SqlAlchemyUserRepository, "get_by_email_in_tenant_for_update", instrumented):
            results = await asyncio.gather(
                reset_password(tenant_id=tenant_id, email=email, new_password=NEW_PASSWORD),
                reset_password(tenant_id=tenant_id, email=email, new_password=NEW_PASSWORD),
                return_exceptions=True,
            )

        exceptions = [r for r in results if isinstance(r, BaseException)]
        assert exceptions == [], f"concorrência não deveria levantar exceção: {exceptions}"

        final_hash = await _user_hash(user_id)
        assert BcryptPasswordHasher().verify(NEW_PASSWORD, final_hash)
        assert await _reset_audit_count(tenant_id, user_id) == 2
        assert await _session_statuses(user_id) == []


class TestDiscoverTenantCandidates:
    """GAP IDENTITY — modo `--discover-tenant`: só leitura, nunca muta nada. Criado porque não há
    (e não vamos criar) nenhum caminho sem SQL para descobrir a qual tenant um e-mail pertence —
    confirmado read-only em todas as asserções abaixo (hash/sessões/auditoria inalterados)."""

    async def test_zero_resultados(self) -> None:
        candidates = await discover_tenant_candidates(email="nao-existe-em-lugar-nenhum@teste.com")
        assert candidates == []

    async def test_exatamente_um_tenant(self, tenants: list[uuid.UUID]) -> None:
        tenant_id = await _create_tenant()
        tenants.append(tenant_id)
        user_id, email = await _create_user(tenant_id, role_ids=frozenset())
        hash_before = await _user_hash(user_id)

        candidates = await discover_tenant_candidates(email=email)

        assert len(candidates) == 1
        assert candidates[0].tenant_id == tenant_id
        assert candidates[0].user_id == user_id
        assert candidates[0].user_status == "ATIVO"
        assert await _user_hash(user_id) == hash_before
        assert await _session_statuses(user_id) == []
        assert await _reset_audit_count(tenant_id, user_id) == 0

    async def test_mesmo_email_dois_tenants(self, tenants: list[uuid.UUID]) -> None:
        tenant_a = await _create_tenant()
        tenants.append(tenant_a)
        tenant_b = await _create_tenant()
        tenants.append(tenant_b)
        shared_email = f"descoberta-{uuid.uuid4().hex[:8]}@teste.com"
        user_a_id = await _create_user_with_email(tenant_a, shared_email)
        user_b_id = await _create_user_with_email(tenant_b, shared_email)

        candidates = await discover_tenant_candidates(email=shared_email)

        assert len(candidates) == 2
        found_tenant_ids = {c.tenant_id for c in candidates}
        assert found_tenant_ids == {tenant_a, tenant_b}
        found_user_ids = {c.user_id for c in candidates}
        assert found_user_ids == {user_a_id, user_b_id}

    async def test_inativo_e_bloqueado_aparecem_com_status_sem_mutacao(
        self, tenants: list[uuid.UUID]
    ) -> None:
        tenant_id = await _create_tenant()
        tenants.append(tenant_id)
        inactive_id, inactive_email = await _create_user(tenant_id, role_ids=frozenset())
        await _deactivate_user(tenant_id, inactive_id)
        blocked_id, blocked_email = await _create_user(tenant_id, role_ids=frozenset())
        await _set_user_status(blocked_id, "BLOQUEADO")

        inactive_hash_before = await _user_hash(inactive_id)
        blocked_hash_before = await _user_hash(blocked_id)

        inactive_candidates = await discover_tenant_candidates(email=inactive_email)
        blocked_candidates = await discover_tenant_candidates(email=blocked_email)

        assert len(inactive_candidates) == 1
        assert inactive_candidates[0].user_status == "INATIVO"
        assert len(blocked_candidates) == 1
        assert blocked_candidates[0].user_status == "BLOQUEADO"

        assert await _user_hash(inactive_id) == inactive_hash_before
        assert await _user_hash(blocked_id) == blocked_hash_before
        assert await _session_statuses(inactive_id) == []
        assert await _session_statuses(blocked_id) == []
        assert await _reset_audit_count(tenant_id, inactive_id) == 0
        assert await _reset_audit_count(tenant_id, blocked_id) == 0


class TestResetUserPasswordCliEntrypoint:
    async def test_confirmacao_divergente_recusada_sem_mutacao(
        self, tenants: list[uuid.UUID], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        tenant_id = await _create_tenant()
        tenants.append(tenant_id)
        user_id, email = await _create_user(tenant_id, role_ids=frozenset())
        hash_before = await _user_hash(user_id)

        from scripts import reset_user_password as cli_module

        passwords = iter([NEW_PASSWORD, "Outra-Senha-Diferente-789"])
        monkeypatch.setattr(cli_module.getpass, "getpass", lambda *_a, **_k: next(passwords))
        monkeypatch.setattr(
            sys, "argv", ["reset_user_password.py", "--tenant-id", str(tenant_id), "--email", email]
        )

        exit_code = await cli_module._main_async()

        assert exit_code == 1
        assert await _user_hash(user_id) == hash_before
        captured = capsys.readouterr()
        assert NEW_PASSWORD not in captured.out
        assert NEW_PASSWORD not in captured.err

    async def test_discover_tenant_flag_nao_pede_senha_nem_muta(
        self, tenants: list[uuid.UUID], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        tenant_id = await _create_tenant()
        tenants.append(tenant_id)
        user_id, email = await _create_user(tenant_id, role_ids=frozenset())
        hash_before = await _user_hash(user_id)

        from scripts import reset_user_password as cli_module

        def _getpass_should_not_be_called(*_a: object, **_k: object) -> str:
            raise AssertionError("--discover-tenant nunca deve pedir senha")

        monkeypatch.setattr(cli_module.getpass, "getpass", _getpass_should_not_be_called)
        monkeypatch.setattr(
            sys, "argv", ["reset_user_password.py", "--discover-tenant", "--email", email]
        )

        exit_code = await cli_module._main_async()

        assert exit_code == 0
        captured = capsys.readouterr()
        assert str(tenant_id) in captured.out
        assert "ATIVO" in captured.out
        assert await _user_hash(user_id) == hash_before
        assert await _session_statuses(user_id) == []
        assert await _reset_audit_count(tenant_id, user_id) == 0

    async def test_tenant_id_obrigatorio_fora_do_discover(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from scripts import reset_user_password as cli_module

        monkeypatch.setattr(
            sys, "argv", ["reset_user_password.py", "--email", "qualquer@teste.com"]
        )

        exit_code = await cli_module._main_async()

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "--tenant-id" in captured.err


async def _create_user_with_email(tenant_id: uuid.UUID, email: str) -> uuid.UUID:
    from modules.identity_access.application.commands.create_user import CreateUserCommand, CreateUserHandler

    bootstrap_actor = AuthenticatedActor(user_id=uuid.uuid4(), tenant_id=tenant_id, session_id=uuid.uuid4())
    token = set_current_tenant_id(tenant_id)
    try:
        dto = await CreateUserHandler().handle(
            CreateUserCommand(
                actor=bootstrap_actor, nome="Usuário de Teste", email=email, password=PASSWORD, driver_id=None,
                employee_id=None, role_ids=frozenset(),
            )
        )
        return dto.id
    finally:
        reset_current_tenant_id(token)
