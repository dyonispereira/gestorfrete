from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.mobile.domain.entities.mobile_device import MobileDevice
from modules.mobile.domain.repositories.mobile_device_repository import MobileDeviceRepository
from modules.mobile.domain.value_objects.device_os import DeviceOS
from modules.mobile.domain.value_objects.device_status import DeviceStatus
from modules.mobile.infrastructure.persistence.models.mobile_device_model import MobileDeviceModel


def _to_entity(model: MobileDeviceModel) -> MobileDevice:
    return MobileDevice(
        id=model.id, motorista_id=model.motorista_id, identificador_dispositivo=model.identificador_dispositivo,
        sistema_operacional=DeviceOS(model.sistema_operacional), versao_so=model.versao_so,
        versao_app=model.versao_app, token_push=model.token_push, status=DeviceStatus(model.status),
        ultimo_acesso_em=model.ultimo_acesso_em,
    )


class SqlAlchemyMobileDeviceRepository(MobileDeviceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> MobileDevice | None:
        tenant_id = get_current_tenant_id()
        stmt = select(MobileDeviceModel).where(MobileDeviceModel.id == id, MobileDeviceModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def get_by_identifier(self, identificador_dispositivo: str) -> MobileDevice | None:
        stmt = select(MobileDeviceModel).where(MobileDeviceModel.identificador_dispositivo == identificador_dispositivo)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def list_page(
        self, *, motorista_id: uuid.UUID, page: int, limit: int
    ) -> tuple[list[MobileDevice], int]:
        tenant_id = get_current_tenant_id()
        stmt = select(MobileDeviceModel).where(
            MobileDeviceModel.tenant_id == tenant_id, MobileDeviceModel.motorista_id == motorista_id
        )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(MobileDeviceModel.ultimo_acesso_em.desc()).offset((page - 1) * limit).limit(limit)
        models = (await self._session.execute(stmt)).scalars().all()
        return [_to_entity(m) for m in models], total

    async def add(self, device: MobileDevice) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(MobileDeviceModel, device.id)
        if model is None:
            model = MobileDeviceModel(id=device.id, tenant_id=tenant_id)
            self._session.add(model)
        model.motorista_id = device.motorista_id
        model.identificador_dispositivo = device.identificador_dispositivo
        model.sistema_operacional = device.sistema_operacional.value
        model.versao_so = device.versao_so
        model.versao_app = device.versao_app
        model.token_push = device.token_push
        model.status = device.status.value
        model.ultimo_acesso_em = device.ultimo_acesso_em
        await self._session.flush()
