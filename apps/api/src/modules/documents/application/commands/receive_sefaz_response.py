from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.exceptions.base import NotFoundError
from modules.documents.application.dtos.cte_dto import CteDTO
from modules.documents.application.fiscal_internal_transitions import FiscalInternalTransitions
from modules.documents.domain.gateways.sefaz_gateway import SefazGateway
from modules.documents.infrastructure.gateways.sandbox_sefaz_gateway import SandboxSefazGateway
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_cte_repository import (
    SqlAlchemyCteRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class ReceiveSefazResponseCommand(Command):
    actor: AuthenticatedActor
    cte_id: uuid.UUID


class ReceiveSefazResponseHandler(CommandHandler[ReceiveSefazResponseCommand, CteDTO]):
    """Lote Fiscal, Parte 2.2 (D397, fechado) — único jeito HTTP de levar um CT-e de `TRANSMITIDO`
    a `AUTORIZADO`/`DENEGADO`. Consulta o `SefazGateway` (hoje sempre `SandboxSefazGateway`, já que
    nenhuma integração real existe) e repassa o resultado para
    `FiscalInternalTransitions.receive_cte_sefaz_response`, que já continha toda a lógica de domínio
    (histórico, Evento Fiscal, sincronização de `Trip.status_fiscal`) — só nunca tinha um jeito real
    de ser acionado. A validação de transição (`TRANSMITIDO→AUTORIZADO` apenas) continua vivendo
    inteiramente em `Cte.authorize()`, chamado por dentro de `receive_cte_sefaz_response`, que
    também levanta `FISCAL_CTE_NOT_FOUND` quando o CT-e não existe — nenhuma checagem duplicada
    aqui."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession], gateway: SefazGateway | None = None) -> None:
        self._session_factory = session_factory
        self._gateway = gateway or SandboxSefazGateway()

    async def handle(self, command: ReceiveSefazResponseCommand) -> CteDTO:
        result = await self._gateway.authorize_cte(cte_id=command.cte_id)
        await FiscalInternalTransitions().receive_cte_sefaz_response(
            cte_id=command.cte_id, approved=result.approved, protocolo_sefaz=result.protocolo_sefaz,
            chave_acesso=result.chave_acesso, xml_arquivo_id=result.xml_arquivo_id,
        )

        async with self._session_factory() as session:
            cte = await SqlAlchemyCteRepository(session).get_by_id(command.cte_id)
        if cte is None:
            raise NotFoundError("FISCAL_CTE_NOT_FOUND", "CT-e não encontrado.")
        return CteDTO.from_entity(cte)
