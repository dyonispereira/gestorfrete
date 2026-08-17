from __future__ import annotations

import uuid
from dataclasses import dataclass

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import AuthorizationError, NotFoundError
from modules.mobile.application.dtos.mobile_device_dto import MobileDeviceDTO
from modules.mobile.domain.value_objects.device_status import DeviceStatus
from modules.mobile.infrastructure.persistence.repositories.sqlalchemy_mobile_device_repository import (
    SqlAlchemyMobileDeviceRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class UpdateMobileDeviceCommand(Command):
    actor: AuthenticatedActor
    driver_id: uuid.UUID
    device_id: uuid.UUID
    os_version: str | None
    app_version: str | None
    push_token: str | None
    status: DeviceStatus | None


class UpdateMobileDeviceHandler(CommandHandler[UpdateMobileDeviceCommand, MobileDeviceDTO]):
    """D302 — atualizar `push_token` aqui nunca dispara efeito de domínio (Auditoria #7); só troca o
    valor guardado, mesmo quando é o único campo do corpo."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: UpdateMobileDeviceCommand) -> MobileDeviceDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            repo = SqlAlchemyMobileDeviceRepository(uow.session)
            device = await repo.get_by_id(command.device_id)
            if device is None:
                raise NotFoundError("MOBILE_DEVICE_NOT_FOUND", "Dispositivo não encontrado.")
            if device.motorista_id != command.driver_id:
                raise AuthorizationError("MOBILE_DEVICE_FORBIDDEN", "Dispositivo não pertence ao Motorista da sessão.")

            device.update_self_service(
                os_version=command.os_version, app_version=command.app_version, push_token=command.push_token,
                status=command.status,
            )
            await repo.add(device)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="dispositivos_mobile",
                entidade_id=device.id, acao="ALTERACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
            )
            await uow.commit()

        return MobileDeviceDTO.from_entity(device)
