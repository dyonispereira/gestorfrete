from __future__ import annotations

from fastapi import Depends

from core.database.session import get_session_factory
from core.exceptions.base import NotFoundError
from interfaces.dependencies.auth import get_current_actor
from modules.mobile.domain.entities.mobile_session import MobileSession
from modules.mobile.infrastructure.persistence.repositories.sqlalchemy_mobile_session_repository import (
    SqlAlchemyMobileSessionRepository,
)
from shared_kernel.domain.actor import AuthenticatedActor


async def get_current_mobile_session(
    actor: AuthenticatedActor = Depends(get_current_actor),
) -> MobileSession:
    """D407 — `actor.session_id` (do JWT) é o mesmo id de `sessoes_mobile`; resolve os dados ricos
    (`motorista_id`/`veiculo_tracionador_id`/`dispositivo_mobile_id`) que `AuthenticatedActor`
    sozinho não carrega."""

    session_factory = get_session_factory()
    async with session_factory() as session:
        repo = SqlAlchemyMobileSessionRepository(session)
        mobile_session = await repo.get_by_id(actor.session_id)
    if mobile_session is None:
        raise NotFoundError("MOBILE_SESSION_NOT_FOUND", "Sessão Mobile não encontrada.")
    return mobile_session
