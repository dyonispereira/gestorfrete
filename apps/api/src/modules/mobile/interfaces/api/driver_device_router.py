from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from core.database.session import get_session_factory
from modules.identity_access.interfaces.dependencies.authorization import require_permission
from modules.mobile.application.commands.update_device import UpdateMobileDeviceCommand, UpdateMobileDeviceHandler
from modules.mobile.application.queries.get_device import GetMobileDeviceHandler, GetMobileDeviceQuery
from modules.mobile.application.queries.list_devices import ListMobileDevicesHandler, ListMobileDevicesQuery
from modules.mobile.domain.entities.mobile_session import MobileSession
from modules.mobile.domain.value_objects.device_status import DeviceStatus
from modules.mobile.interfaces.dependencies import get_current_mobile_session
from modules.mobile.interfaces.schemas.device_schemas import MobileDeviceResponse, UpdateMobileDeviceRequest
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/mobile/devices", tags=["Mobile Devices"])


@router.get("")
async def list_devices(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    actor: AuthenticatedActor = Depends(require_permission("mobile.device.view_own")),
    mobile_session: MobileSession = Depends(get_current_mobile_session),
) -> dict[str, Any]:
    handler = ListMobileDevicesHandler(get_session_factory())
    result = await handler.handle(
        ListMobileDevicesQuery(actor=actor, driver_id=mobile_session.motorista_id, page=page, limit=limit)
    )
    return {
        "data": [MobileDeviceResponse.from_dto(d) for d in result.items],
        "meta": {"pagination": {"page": page, "limit": limit, "total": result.total}},
    }


@router.get("/{device_id}", response_model=MobileDeviceResponse)
async def get_device(
    device_id: uuid.UUID, actor: AuthenticatedActor = Depends(require_permission("mobile.device.view_own")),
    mobile_session: MobileSession = Depends(get_current_mobile_session),
) -> MobileDeviceResponse:
    handler = GetMobileDeviceHandler(get_session_factory())
    dto = await handler.handle(
        GetMobileDeviceQuery(actor=actor, driver_id=mobile_session.motorista_id, device_id=device_id)
    )
    return MobileDeviceResponse.from_dto(dto)


@router.patch("/{device_id}", response_model=MobileDeviceResponse)
async def update_device(
    device_id: uuid.UUID, body: UpdateMobileDeviceRequest,
    actor: AuthenticatedActor = Depends(require_permission("mobile.device.edit_own")),
    mobile_session: MobileSession = Depends(get_current_mobile_session),
) -> MobileDeviceResponse:
    handler = UpdateMobileDeviceHandler()
    status = DeviceStatus(body.status) if body.status is not None else None
    dto = await handler.handle(
        UpdateMobileDeviceCommand(
            actor=actor, driver_id=mobile_session.motorista_id, device_id=device_id, os_version=body.os_version,
            app_version=body.app_version, push_token=body.push_token, status=status,
        )
    )
    return MobileDeviceResponse.from_dto(dto)
