from __future__ import annotations

from fastapi import APIRouter, Depends

from core.config.settings import Settings, get_settings
from core.database.session import get_session_factory
from interfaces.dependencies.auth import get_current_actor
from modules.mobile.application.commands.login import MobileLoginCommand, MobileLoginHandler
from modules.mobile.application.commands.logout import MobileLogoutCommand, MobileLogoutHandler
from modules.mobile.application.commands.refresh import MobileRefreshCommand, MobileRefreshHandler
from modules.mobile.application.queries.get_current_session import GetCurrentSessionHandler, GetCurrentSessionQuery
from modules.mobile.domain.value_objects.auth_method import AuthMethod
from modules.mobile.domain.value_objects.device_os import DeviceOS
from modules.mobile.interfaces.schemas.auth_schemas import (
    MobileLoginRequest,
    MobileLoginResponse,
    MobileMeResponse,
    MobileRefreshRequest,
    TokenPairResponse,
)
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/mobile/auth", tags=["Mobile Authentication"])


@router.post("/login", response_model=MobileLoginResponse)
async def login(body: MobileLoginRequest, settings: Settings = Depends(get_settings)) -> MobileLoginResponse:
    handler = MobileLoginHandler(settings)
    result = await handler.handle(
        MobileLoginCommand(
            cpf=body.cpf, vehicle_plate=body.vehicle_plate or "", auth_method=AuthMethod(body.auth_method),
            credential=body.credential, device_identifier=body.device.device_identifier,
            device_os=DeviceOS(body.device.os), device_os_version=body.device.os_version,
            device_app_version=body.device.app_version, device_push_token=body.device.push_token,
        )
    )
    return MobileLoginResponse.from_login_dto(result)


@router.post("/refresh", response_model=TokenPairResponse)
async def refresh(body: MobileRefreshRequest, settings: Settings = Depends(get_settings)) -> TokenPairResponse:
    handler = MobileRefreshHandler(settings)
    result = await handler.handle(MobileRefreshCommand(refresh_token=body.refresh_token))
    return TokenPairResponse.from_dto(result)


@router.post("/logout", status_code=204, response_model=None)
async def logout(actor: AuthenticatedActor = Depends(get_current_actor)) -> None:
    handler = MobileLogoutHandler()
    await handler.handle(MobileLogoutCommand(actor=actor))


@router.get("/me", response_model=MobileMeResponse)
async def me(actor: AuthenticatedActor = Depends(get_current_actor)) -> MobileMeResponse:
    handler = GetCurrentSessionHandler(get_session_factory())
    result = await handler.handle(GetCurrentSessionQuery(actor=actor))
    return MobileMeResponse.from_result(result)
