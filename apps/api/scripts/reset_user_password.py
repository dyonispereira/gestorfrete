#!/usr/bin/env python3
"""GAP IDENTITY (Gate 6) — ferramenta operacional de recuperação de credencial.

Resolve apenas "tenant + usuário já existem, operador perdeu a senha" (GAP A). Não resolve
bootstrap de primeiro admin de um tenant novo (GAP B, backlog separado) e deliberadamente não cria
nenhum caminho HTTP paralelo de autenticação — isto só existe como comando executado por um
operador com acesso direto ao ambiente da aplicação (mesmo `DATABASE_URL` que a API usa).

Uso (reset real):
    poetry run python scripts/reset_user_password.py --tenant-id <uuid> --email <email>

Uso (descoberta — só leitura, nunca muta nada, nunca pede senha):
    poetry run python scripts/reset_user_password.py --discover-tenant --email <email>

A nova senha é sempre pedida interativamente (nunca como argumento de linha de comando, para não
ficar exposta em histórico de shell/`ps`).
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.audit.audit_logger import AuditLogger  # noqa: E402
from core.database.unit_of_work import SQLAlchemyUnitOfWork  # noqa: E402
from core.exceptions.base import ApplicationError, ConflictError, NotFoundError, ValidationError  # noqa: E402
from core.multitenancy.context import reset_current_tenant_id, set_current_tenant_id  # noqa: E402
from core.security.password_hasher import BcryptPasswordHasher  # noqa: E402
from modules.identity_access.domain.value_objects.enums import SessionEndedReason, UserStatus  # noqa: E402
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_session_repository import (  # noqa: E402
    SqlAlchemySessionRepository,
)
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_user_repository import (  # noqa: E402
    SqlAlchemyUserRepository,
)
from modules.tenancy.infrastructure.persistence.repositories.sqlalchemy_tenant_repository import (  # noqa: E402
    SqlAlchemyTenantRepository,
)

MIN_PASSWORD_LENGTH = 8
OPERATOR_LABEL = "CLI reset-user-password"
_RESETTABLE_STATUSES = frozenset({UserStatus.ATIVO})


@dataclass(frozen=True)
class TenantCandidate:
    """Um resultado de `--discover-tenant` — só o suficiente para o operador conferir visualmente
    qual `--tenant-id` usar no reset real, nunca dado sensível (sem hash, sem e-mail duplicado
    exposto além do que o operador já informou)."""

    tenant_id: uuid.UUID
    tenant_codigo: str
    user_id: uuid.UUID
    user_status: str


async def discover_tenant_candidates(*, email: str) -> list[TenantCandidate]:
    """Modo administrativo read-only — nunca muta nada, nunca pede senha, nunca escolhe um tenant
    automaticamente para reset. Existe porque o mesmo e-mail pode existir em tenants diferentes
    (`uq_usuarios_tenant_id_email` é só por tenant) e não há, hoje, nenhum outro caminho sem SQL
    para um operador descobrir a qual tenant um e-mail pertence."""

    async with SQLAlchemyUnitOfWork() as uow:
        user_repo = SqlAlchemyUserRepository(uow.session)
        tenant_repo = SqlAlchemyTenantRepository(uow.session)
        matches = await user_repo.find_tenant_candidates_by_email(email)

        candidates: list[TenantCandidate] = []
        for user, tenant_id in matches:
            tenant = await tenant_repo.get_by_id(tenant_id)
            tenant_codigo = tenant.codigo if tenant is not None else "(tenant não encontrado)"
            candidates.append(
                TenantCandidate(
                    tenant_id=tenant_id, tenant_codigo=tenant_codigo, user_id=user.id, user_status=user.status.value
                )
            )
        return candidates


async def reset_password(*, tenant_id: uuid.UUID, email: str, new_password: str) -> None:
    """Núcleo atômico da operação — sem I/O de terminal, chamado tanto pelo `main()` interativo
    quanto diretamente pelos testes de integração. Qualquer falha levanta `ApplicationError` (um
    dos tipos já usados pelo resto da aplicação) antes de qualquer `commit()`; a própria
    `SQLAlchemyUnitOfWork` faz rollback automático de tudo (hash, sessões, auditoria) nesse caso —
    nenhum caminho deixa mutação parcial.
    """

    if len(new_password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            "IDENTITY_PASSWORD_TOO_SHORT", f"Senha deve ter ao menos {MIN_PASSWORD_LENGTH} caracteres."
        )

    async with SQLAlchemyUnitOfWork() as uow:
        tenant_repo = SqlAlchemyTenantRepository(uow.session)
        tenant = await tenant_repo.get_by_id(tenant_id)
        if tenant is None:
            raise NotFoundError("TENANCY_TENANT_NOT_FOUND", f"Tenant {tenant_id} não encontrado.")

        token = set_current_tenant_id(tenant_id)
        try:
            user_repo = SqlAlchemyUserRepository(uow.session)
            user = await user_repo.get_by_email_in_tenant_for_update(email)
            if user is None:
                raise NotFoundError(
                    "IDENTITY_USER_NOT_FOUND", f"Usuário {email} não encontrado no tenant {tenant_id}."
                )

            if user.status not in _RESETTABLE_STATUSES:
                raise ConflictError(
                    "IDENTITY_USER_NOT_RESETTABLE",
                    f"Usuário está {user.status.value} — reset de senha não permitido por este "
                    "comando. Reativação/desbloqueio é uma ação administrativa separada.",
                )

            now = datetime.now(timezone.utc)
            hasher = BcryptPasswordHasher()
            user.change_password_hash(senha_hash=hasher.hash(new_password), updated_by=None, now=now)
            await user_repo.add(user)

            session_repo = SqlAlchemySessionRepository(uow.session)
            await session_repo.end_all_active_for_user(user.id, SessionEndedReason.PASSWORD_RESET)

            await AuditLogger().record(
                uow.session,
                tenant_id=tenant_id,
                entidade_tipo="usuarios",
                entidade_id=user.id,
                acao="ALTERACAO",
                ator_id=None,
                ator_nome_snapshot=OPERATOR_LABEL,
                origem="SISTEMA",
                motivo="Reset administrativo de senha via CLI operacional.",
            )

            await uow.commit()
        finally:
            reset_current_tenant_id(token)


async def _main_async() -> int:
    parser = argparse.ArgumentParser(description="Reset operacional de senha de um usuário existente.")
    parser.add_argument("--tenant-id", required=False, type=uuid.UUID, default=None)
    parser.add_argument("--email", required=True)
    parser.add_argument(
        "--discover-tenant",
        action="store_true",
        help="Modo read-only: lista os tenants onde este e-mail existe, sem alterar nada e sem pedir senha.",
    )
    args = parser.parse_args()

    if args.discover_tenant:
        candidates = await discover_tenant_candidates(email=args.email)
        if not candidates:
            print(f"Nenhum tenant encontrado para {args.email}.")
            return 0

        print(f"{len(candidates)} tenant(s) encontrado(s) para {args.email}:")
        for c in candidates:
            print(f"  tenant_id={c.tenant_id}  tenant_codigo={c.tenant_codigo}  status={c.user_status}")

        if len(candidates) > 1:
            print(
                "\nMais de um tenant com este e-mail — rode o reset novamente passando "
                "explicitamente o --tenant-id correto (não há escolha automática)."
            )
        else:
            print(
                f"\nPara resetar, rode: --tenant-id {candidates[0].tenant_id} --email {args.email} "
                "(sem --discover-tenant)."
            )
        return 0

    if args.tenant_id is None:
        print("--tenant-id é obrigatório fora do modo --discover-tenant.", file=sys.stderr)
        return 1

    new_password = getpass.getpass("Nova senha: ")
    confirm_password = getpass.getpass("Confirme a nova senha: ")
    if new_password != confirm_password:
        print("As senhas informadas não coincidem.", file=sys.stderr)
        return 1

    try:
        await reset_password(tenant_id=args.tenant_id, email=args.email, new_password=new_password)
    except ApplicationError as exc:
        print(f"Falha ({exc.code}): {exc.message}", file=sys.stderr)
        return 1

    print(f"Senha redefinida para {args.email} (tenant {args.tenant_id}). Todas as sessões ativas foram encerradas.")
    return 0


def main() -> None:
    sys.exit(asyncio.run(_main_async()))


if __name__ == "__main__":
    main()
