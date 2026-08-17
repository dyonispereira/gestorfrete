from __future__ import annotations

from fastapi import APIRouter, Depends

from core.config.settings import Settings, get_settings
from core.database.session import get_session_factory
from interfaces.dependencies.auth import get_current_actor
from modules.identity_access.application.commands.login import LoginCommand, LoginHandler
from modules.identity_access.application.commands.logout import LogoutCommand, LogoutHandler
from modules.identity_access.application.commands.refresh_token import (
    RefreshTokenCommand,
    RefreshTokenHandler,
)
from modules.identity_access.application.queries.get_me import GetMeHandler, GetMeQuery
from modules.identity_access.interfaces.schemas.auth_schemas import (
    LoginRequest,
    LoginResponse,
    MeResponse,
    RefreshRequest,
    TokenPairResponse,
)
from shared_kernel.domain.actor import AuthenticatedActor

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, settings: Settings = Depends(get_settings)) -> LoginResponse:
    handler = LoginHandler(settings)
    result = await handler.handle(LoginCommand(email=body.email, password=body.password))
    return LoginResponse.from_login_dto(result)


@router.post("/refresh", response_model=TokenPairResponse)
async def refresh(body: RefreshRequest, settings: Settings = Depends(get_settings)) -> TokenPairResponse:
    handler = RefreshTokenHandler(settings)
    result = await handler.handle(RefreshTokenCommand(refresh_token=body.refresh_token))
    return TokenPairResponse.from_dto(result)


@router.post("/logout", status_code=204, response_model=None)
async def logout(actor: AuthenticatedActor = Depends(get_current_actor)) -> None:
    handler = LogoutHandler()
    await handler.handle(LogoutCommand(actor=actor))


@router.get("/me", response_model=MeResponse)
async def me(actor: AuthenticatedActor = Depends(get_current_actor)) -> MeResponse:
    handler = GetMeHandler(get_session_factory())
    result = await handler.handle(GetMeQuery(actor=actor))
    return MeResponse.from_dto(result)
