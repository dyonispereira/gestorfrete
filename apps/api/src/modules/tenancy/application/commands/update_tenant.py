from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, InfrastructureError
from modules.tenancy.application.dtos.tenant_dto import TenantDTO
from modules.tenancy.infrastructure.persistence.repositories.sqlalchemy_tenant_repository import (
    SqlAlchemyTenantRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateTenantCommand(Command):
    actor: AuthenticatedActor
    razao_social: str | None
    cnpj: str | None


class UpdateTenantHandler(CommandHandler[UpdateTenantCommand, TenantDTO]):
    """D342 — o Handler abre e controla o UnitOfWork; `SqlAlchemyTenantRepository` nunca chama
    `session.commit()` por conta própria."""

    async def handle(self, command: UpdateTenantCommand) -> TenantDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyTenantRepository(uow.session)

            tenant = await repo.get_by_id(command.actor.tenant_id)
            if tenant is None:
                raise InfrastructureError(
                    "TENANCY_CONTEXT_TENANT_MISSING",
                    "O tenant do contexto autenticado não foi encontrado.",
                )

            if command.cnpj is not None and await repo.exists_with_cnpj(
                command.cnpj, excluding_id=tenant.id
            ):
                raise ConflictError(
                    "TENANCY_CNPJ_ALREADY_EXISTS", "CNPJ já cadastrado na plataforma."
                )

            tenant.update_company_data(
                razao_social=command.razao_social,
                cnpj=command.cnpj,
                updated_by=command.actor.user_id,
                now=datetime.now(timezone.utc),
            )
            await repo.add(tenant)
            await uow.commit()

        return TenantDTO.from_entity(tenant)
