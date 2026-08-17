from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from core.audit.audit_logger import AuditLogger
from core.config.settings import Settings
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import AuthenticationError, AuthorizationError
from core.multitenancy.context import reset_current_tenant_id, set_current_tenant_id
from core.security.jwt_token_service import JWTTokenService
from core.security.token_hasher import hash_token
from modules.drivers.application.dtos.driver_dto import DriverDTO
from modules.drivers.domain.entities.driver import Driver
from modules.drivers.domain.value_objects.fitness_status import FitnessStatus
from modules.drivers.infrastructure.persistence.repositories.sqlalchemy_driver_repository import (
    SqlAlchemyDriverRepository,
)
from modules.fleet.domain.entities.vehicle import Vehicle
from modules.fleet.domain.value_objects.vehicle_status import VehicleStatus
from modules.fleet.infrastructure.persistence.repositories.sqlalchemy_vehicle_repository import (
    SqlAlchemyVehicleRepository,
)
from modules.identity_access.domain.entities.session import Session
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_session_repository import (
    SqlAlchemySessionRepository,
)
from modules.identity_access.infrastructure.persistence.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from modules.mobile.application.dtos.mobile_login_result_dto import MobileLoginResultDTO
from modules.mobile.application.dtos.mobile_session_dto import MobileSessionDTO
from modules.mobile.domain.entities.mobile_device import MobileDevice
from modules.mobile.domain.entities.mobile_session import MobileSession
from modules.mobile.domain.value_objects.auth_method import AuthMethod
from modules.mobile.domain.value_objects.device_os import DeviceOS
from modules.mobile.domain.value_objects.device_status import DeviceStatus
from modules.mobile.infrastructure.persistence.repositories.sqlalchemy_mobile_device_repository import (
    SqlAlchemyMobileDeviceRepository,
)
from modules.mobile.infrastructure.persistence.repositories.sqlalchemy_mobile_session_repository import (
    SqlAlchemyMobileSessionRepository,
)
from shared_kernel.application.command import Command, CommandHandler

SESSION_TTL_MINUTES = 60 * 8
"""Mesma janela de `identity_access.application.commands.login.SESSION_TTL_MINUTES` — a Sessão
Mobile compartilha o mesmo período de validade da `Sessão` subjacente (D407)."""


@dataclass(frozen=True)
class MobileLoginCommand(Command):
    cpf: str
    vehicle_plate: str
    auth_method: AuthMethod
    credential: str  # D409 — aceito, nunca validado para CPF_VEICULO
    device_identifier: str
    device_os: DeviceOS
    device_os_version: str | None
    device_app_version: str
    device_push_token: str | None


class MobileLoginHandler(CommandHandler[MobileLoginCommand, MobileLoginResultDTO]):
    """D407/D408/D409 — ver `docs/backend/mobile/AUTHENTICATION_AND_DEVICE_IMPLEMENTATION.md`."""

    def __init__(self, settings: Settings, audit_logger: AuditLogger | None = None) -> None:
        self._settings = settings
        self._token_service = JWTTokenService(settings)
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: MobileLoginCommand) -> MobileLoginResultDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            driver_repo = SqlAlchemyDriverRepository(uow.session)
            vehicle_repo = SqlAlchemyVehicleRepository(uow.session)
            user_repo = SqlAlchemyUserRepository(uow.session)

            candidates = await driver_repo.list_by_cpf_across_tenants(command.cpf)
            resolved: tuple[Driver, uuid.UUID, Vehicle] | None = None
            for candidate_driver, candidate_tenant_id in candidates:
                vehicle = await vehicle_repo.get_by_placa_and_tenant(command.vehicle_plate, candidate_tenant_id)
                if vehicle is not None and vehicle.status == VehicleStatus.ATIVO:
                    if resolved is not None:
                        # D408 — mais de um par (CPF, Placa, tenant) válido é tratado como falha de
                        # login, nunca uma escolha silenciosa entre tenants.
                        raise AuthenticationError("MOBILE_LOGIN_INVALID_CREDENTIALS", "Credenciais inválidas.")
                    resolved = (candidate_driver, candidate_tenant_id, vehicle)

            if resolved is None:
                raise AuthenticationError("MOBILE_LOGIN_INVALID_CREDENTIALS", "Credenciais inválidas.")
            driver, tenant_id, vehicle = resolved

            if driver.fitness_status == FitnessStatus.BLOQUEADO:
                raise AuthorizationError("MOBILE_DRIVER_BLOCKED", "Motorista bloqueado.")

            user = await user_repo.get_by_driver_id_and_tenant(driver.id, tenant_id)
            if user is None:
                raise AuthenticationError("MOBILE_LOGIN_INVALID_CREDENTIALS", "Credenciais inválidas.")

            now = datetime.now(timezone.utc)
            token = set_current_tenant_id(tenant_id)
            try:
                device_repo = SqlAlchemyMobileDeviceRepository(uow.session)
                session_repo = SqlAlchemyMobileSessionRepository(uow.session)
                identity_session_repo = SqlAlchemySessionRepository(uow.session)

                device = await device_repo.get_by_identifier(command.device_identifier)
                if device is None:
                    device = MobileDevice.register(
                        motorista_id=driver.id, identificador_dispositivo=command.device_identifier,
                        sistema_operacional=command.device_os, versao_so=command.device_os_version,
                        versao_app=command.device_app_version, token_push=command.device_push_token, now=now,
                    )
                else:
                    # Auditoria #4 — dispositivo INATIVO/REVOGADO nunca permite nova Sessão, mesmo
                    # com CPF+Placa+Motorista Apto corretos; independente da Sessão (D132), na
                    # direção oposta (o Dispositivo pode bloquear login, a Sessão nunca bloqueia o
                    # Dispositivo).
                    if device.status != DeviceStatus.ATIVO:
                        raise AuthorizationError("MOBILE_DEVICE_BLOCKED", "Dispositivo inativo ou revogado.")
                    device.update_self_service(
                        os_version=command.device_os_version, app_version=command.device_app_version,
                        push_token=command.device_push_token, status=None,
                    )
                    device.touch_access(now)
                await device_repo.add(device)

                identity_session = Session.start(
                    user_id=user.id, started_at=now, expires_at=now + timedelta(minutes=SESSION_TTL_MINUTES)
                )
                await identity_session_repo.add(identity_session)

                access_token, refresh_token, expires_in = self._issue_tokens(
                    user_id=user.id, tenant_id=tenant_id, session_id=identity_session.id
                )

                mobile_session = MobileSession.start(
                    id=identity_session.id, motorista_id=driver.id, veiculo_tracionador_id=vehicle.id,
                    dispositivo_mobile_id=device.id, metodo_autenticacao=command.auth_method,
                    token_acesso_hash=hash_token(access_token), started_at=now, expires_at=identity_session.expires_at,
                )
                await session_repo.add(mobile_session)

                await self._audit.record(
                    uow.session, tenant_id=tenant_id, entidade_tipo="sessoes_mobile", entidade_id=mobile_session.id,
                    acao="LOGIN", ator_id=user.id, ator_nome_snapshot=driver.nome,
                )
            finally:
                reset_current_tenant_id(token)

            await uow.commit()

        return MobileLoginResultDTO(
            session=MobileSessionDTO.from_entity(mobile_session), driver=DriverDTO.from_entity(driver),
            access_token=access_token, refresh_token=refresh_token, expires_in=expires_in,
        )

    def _issue_tokens(
        self, *, user_id: uuid.UUID, tenant_id: uuid.UUID, session_id: uuid.UUID
    ) -> tuple[str, str, int]:
        claims = {"tenant_id": str(tenant_id), "session_id": str(session_id)}
        access_token = self._token_service.issue_access_token(subject=str(user_id), claims=claims)
        refresh_token = self._token_service.issue_access_token(
            subject=str(user_id), claims={**claims, "purpose": "refresh"}
        )
        expires_in = self._settings.jwt_access_token_expire_minutes * 60
        return access_token, refresh_token, expires_in
