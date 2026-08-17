from __future__ import annotations

from dataclasses import dataclass

from modules.drivers.application.dtos.driver_dto import DriverDTO
from modules.mobile.application.dtos.mobile_session_dto import MobileSessionDTO


@dataclass(frozen=True)
class MobileLoginResultDTO:
    session: MobileSessionDTO
    driver: DriverDTO
    access_token: str
    refresh_token: str
    expires_in: int
