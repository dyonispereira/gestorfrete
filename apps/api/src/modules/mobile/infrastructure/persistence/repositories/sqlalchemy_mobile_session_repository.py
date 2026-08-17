from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.multitenancy.context import get_current_tenant_id
from modules.mobile.domain.entities.mobile_session import MobileSession
from modules.mobile.domain.repositories.mobile_session_repository import MobileSessionRepository
from modules.mobile.domain.value_objects.auth_method import AuthMethod
from modules.mobile.domain.value_objects.mobile_session_end_reason import MobileSessionEndReason
from modules.mobile.domain.value_objects.mobile_session_status import MobileSessionStatus
from modules.mobile.infrastructure.persistence.models.mobile_session_model import MobileSessionModel


def _to_entity(model: MobileSessionModel) -> MobileSession:
    return MobileSession(
        id=model.id, motorista_id=model.motorista_id, veiculo_tracionador_id=model.veiculo_tracionador_id,
        dispositivo_mobile_id=model.dispositivo_mobile_id,
        metodo_autenticacao=AuthMethod(model.metodo_autenticacao), token_acesso_hash=model.token_acesso_hash,
        data_hora_inicio=model.data_hora_inicio, data_hora_expiracao_prevista=model.data_hora_expiracao_prevista,
        data_hora_encerramento=model.data_hora_encerramento,
        motivo_encerramento=MobileSessionEndReason(model.motivo_encerramento) if model.motivo_encerramento else None,
        revogado_por=model.revogado_por, status=MobileSessionStatus(model.status),
    )


class SqlAlchemyMobileSessionRepository(MobileSessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> MobileSession | None:
        tenant_id = get_current_tenant_id()
        stmt = select(MobileSessionModel).where(MobileSessionModel.id == id, MobileSessionModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def add(self, session: MobileSession) -> None:
        tenant_id = get_current_tenant_id()
        model = await self._session.get(MobileSessionModel, session.id)
        if model is None:
            model = MobileSessionModel(id=session.id, tenant_id=tenant_id)
            self._session.add(model)
        model.motorista_id = session.motorista_id
        model.veiculo_tracionador_id = session.veiculo_tracionador_id
        model.dispositivo_mobile_id = session.dispositivo_mobile_id
        model.metodo_autenticacao = session.metodo_autenticacao.value
        model.token_acesso_hash = session.token_acesso_hash
        model.data_hora_inicio = session.data_hora_inicio
        model.data_hora_expiracao_prevista = session.data_hora_expiracao_prevista
        model.data_hora_encerramento = session.data_hora_encerramento
        model.motivo_encerramento = session.motivo_encerramento.value if session.motivo_encerramento else None
        model.revogado_por = session.revogado_por
        model.status = session.status.value
        await self._session.flush()
