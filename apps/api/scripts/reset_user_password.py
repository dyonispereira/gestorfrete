#!/usr/bin/env python3
"""GAP IDENTITY (Gate 6) — ferramenta operacional de recuperação de credencial.

Resolve apenas "tenant + usuário já existem, operador perdeu a senha" (GAP A). Não resolve
bootstrap de primeiro admin de um tenant novo (GAP B, backlog separado) e deliberadamente não cria
nenhum caminho HTTP paralelo de autenticação — isto só existe como comando executado por um
operador com acesso direto ao ambiente da aplicação (mesmo `DATABASE_URL` que a API usa).

Uso:
    PYTHONPATH=src poetry run python scripts/reset_user_password.py \\
        --tenant-id <uuid> --email <email>

A nova senha é sempre pedida interativamente (nunca como argumento de linha de comando, para não
ficar exposta em histórico de shell/`ps`).
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import sys
import uuid
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
    parser.add_argument("--tenant-id", required=True, type=uuid.UUID)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()

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
