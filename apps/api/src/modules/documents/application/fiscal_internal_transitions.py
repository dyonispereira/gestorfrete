from __future__ import annotations

import uuid
from datetime import datetime, timezone

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.documents.domain.entities.cte_status_history_entry import CteStatusHistoryEntry
from modules.documents.domain.entities.fiscal_event import FiscalEvent
from modules.documents.domain.entities.mdfe_status_history_entry import MdfeStatusHistoryEntry
from modules.documents.domain.value_objects.fiscal_event_document_type import FiscalEventDocumentType
from modules.documents.domain.value_objects.fiscal_event_result import FiscalEventResult
from modules.documents.domain.value_objects.fiscal_event_type import FiscalEventType
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_cte_repository import (
    SqlAlchemyCteRepository,
)
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_cte_status_history_repository import (
    SqlAlchemyCteStatusHistoryRepository,
)
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_fiscal_event_repository import (
    SqlAlchemyFiscalEventRepository,
)
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_mdfe_repository import (
    SqlAlchemyMdfeRepository,
)
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_mdfe_status_history_repository import (
    SqlAlchemyMdfeStatusHistoryRepository,
)
from modules.freight.application.trip_internal_transitions import TripInternalTransitions
from modules.freight.domain.value_objects.trip_fiscal_status import TripFiscalStatus


class FiscalInternalTransitions:
    """D397 — simula as duas transições genuinamente externas deste lote (resposta assíncrona da
    SEFAZ): CT-e `TRANSMITIDO→AUTORIZADO`/`DENEGADO` e MDF-e `PENDENTE→AUTORIZADO`. Nenhum método
    aqui é acionável por HTTP — mesmo padrão de `TripInternalTransitions` (D376). Testes chamam estes
    métodos diretamente para simular a resposta e exercitar o restante da máquina de estados."""

    async def receive_cte_sefaz_response(
        self,
        *,
        cte_id: uuid.UUID,
        approved: bool,
        protocolo_sefaz: str,
        chave_acesso: str | None = None,
        xml_arquivo_id: uuid.UUID | None = None,
        payload_arquivo_id: uuid.UUID | None = None,
        now: datetime | None = None,
    ) -> None:
        now = now or datetime.now(timezone.utc)
        async with SQLAlchemyUnitOfWork() as uow:
            cte_repo = SqlAlchemyCteRepository(uow.session)
            history_repo = SqlAlchemyCteStatusHistoryRepository(uow.session)
            event_repo = SqlAlchemyFiscalEventRepository(uow.session)

            cte = await cte_repo.get_by_id(cte_id)
            if cte is None:
                raise NotFoundError("FISCAL_CTE_NOT_FOUND", "CT-e não encontrado.")

            # D108/D275 — idempotência de domínio: reprocessar o mesmo protocolo nunca gera uma
            # segunda transição nem um segundo Evento Fiscal, mesmo se o Idempotency-Key HTTP do
            # comando de origem não tiver sido reaproveitado.
            already_processed = await event_repo.exists_with_protocol(
                documento_tipo=FiscalEventDocumentType.CTE.value, documento_id=cte_id,
                protocolo_externo=protocolo_sefaz,
            )
            if already_processed or cte.protocolo_sefaz == protocolo_sefaz:
                return

            if approved:
                # D107 — `xml_arquivo_id` é obrigatório (aplicação) a partir de `AUTORIZADO`
                # (dictionary/007-fiscal.md), mesmo a coluna física sendo nullable — gerado aqui
                # quando o chamador não informa um real, mesmo padrão de `payload_arquivo_id` do
                # próprio `EventoFiscal` abaixo.
                cte.authorize(
                    protocolo_sefaz=protocolo_sefaz, chave_acesso=chave_acesso or "",
                    xml_arquivo_id=xml_arquivo_id or uuid.uuid4(), now=now,
                )
            else:
                cte.deny(protocolo_sefaz=protocolo_sefaz, now=now)
            await cte_repo.add(cte)

            await history_repo.add(
                CteStatusHistoryEntry.create(
                    cte_id=cte.id, status=cte.status.value, usuario_id=None, origem="documents", now=now,
                    observacao=None if approved else "Denegado pela SEFAZ.",
                )
            )
            await event_repo.add(
                FiscalEvent.create(
                    documento_tipo=FiscalEventDocumentType.CTE, documento_id=cte.id,
                    tipo_evento=FiscalEventType.RESPOSTA, payload_arquivo_id=payload_arquivo_id or uuid.uuid4(),
                    protocolo_externo=protocolo_sefaz, numero_tentativa=1,
                    resultado=FiscalEventResult.SUCESSO if approved else FiscalEventResult.FALHA,
                    origem="documents", data_hora_inicio=now, data_hora_fim=now,
                )
            )
            await uow.commit()

        if approved:
            await TripInternalTransitions().record_fiscal_transition(
                trip_id=cte.viagem_id, status=TripFiscalStatus.CTE_EMITIDO, now=now
            )

    async def receive_mdfe_sefaz_response(
        self,
        *,
        mdfe_id: uuid.UUID,
        protocolo_sefaz: str,
        chave_acesso: str | None = None,
        xml_arquivo_id: uuid.UUID | None = None,
        payload_arquivo_id: uuid.UUID | None = None,
        now: datetime | None = None,
    ) -> None:
        now = now or datetime.now(timezone.utc)
        async with SQLAlchemyUnitOfWork() as uow:
            mdfe_repo = SqlAlchemyMdfeRepository(uow.session)
            history_repo = SqlAlchemyMdfeStatusHistoryRepository(uow.session)
            event_repo = SqlAlchemyFiscalEventRepository(uow.session)

            mdfe = await mdfe_repo.get_by_id(mdfe_id)
            if mdfe is None:
                raise NotFoundError("FISCAL_MDFE_NOT_FOUND", "MDF-e não encontrado.")

            already_processed = await event_repo.exists_with_protocol(
                documento_tipo=FiscalEventDocumentType.MDFE.value, documento_id=mdfe_id,
                protocolo_externo=protocolo_sefaz,
            )
            if already_processed or mdfe.protocolo_sefaz == protocolo_sefaz:
                return

            mdfe.authorize(
                protocolo_sefaz=protocolo_sefaz, chave_acesso=chave_acesso or "",
                xml_arquivo_id=xml_arquivo_id or uuid.uuid4(),
            )
            await mdfe_repo.add(mdfe)

            await history_repo.add(
                MdfeStatusHistoryEntry.create(
                    mdfe_id=mdfe.id, status=mdfe.status.value, usuario_id=None, origem="documents", now=now,
                )
            )
            await event_repo.add(
                FiscalEvent.create(
                    documento_tipo=FiscalEventDocumentType.MDFE, documento_id=mdfe.id,
                    tipo_evento=FiscalEventType.RESPOSTA, payload_arquivo_id=payload_arquivo_id or uuid.uuid4(),
                    protocolo_externo=protocolo_sefaz, numero_tentativa=1, resultado=FiscalEventResult.SUCESSO,
                    origem="documents", data_hora_inicio=now, data_hora_fim=now,
                )
            )
            await uow.commit()

        await TripInternalTransitions().record_fiscal_transition(
            trip_id=mdfe.viagem_id, status=TripFiscalStatus.MDFE_EMITIDO, now=now
        )
