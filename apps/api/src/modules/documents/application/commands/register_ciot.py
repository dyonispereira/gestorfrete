from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError
from modules.documents.application.dtos.ciot_dto import CiotDTO
from modules.documents.domain.entities.ciot_status_history_entry import CiotStatusHistoryEntry
from modules.documents.domain.entities.fiscal_event import FiscalEvent
from modules.documents.domain.value_objects.fiscal_event_document_type import FiscalEventDocumentType
from modules.documents.domain.value_objects.fiscal_event_result import FiscalEventResult
from modules.documents.domain.value_objects.fiscal_event_type import FiscalEventType
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_ciot_repository import (
    SqlAlchemyCiotRepository,
)
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_ciot_status_history_repository import (
    SqlAlchemyCiotStatusHistoryRepository,
)
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_fiscal_event_repository import (
    SqlAlchemyFiscalEventRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class RegisterCiotCommand(Command):
    actor: AuthenticatedActor
    ciot_id: uuid.UUID


class RegisterCiotHandler(CommandHandler[RegisterCiotCommand, CiotDTO]):
    """`PENDENTE→REGISTRADO` — D397: chamada síncrona real (submete à ANTT e já recebe `codigo_
    ciot`/`protocolo_antt` na mesma resposta HTTP, sem passo assíncrono separado como CT-e/MDF-e).
    Ainda assim grava um `EventoFiscal` para manter a mesma observabilidade (D115)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: RegisterCiotCommand) -> CiotDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            ciot_repo = SqlAlchemyCiotRepository(uow.session)
            history_repo = SqlAlchemyCiotStatusHistoryRepository(uow.session)
            event_repo = SqlAlchemyFiscalEventRepository(uow.session)

            ciot = await ciot_repo.get_by_id(command.ciot_id)
            if ciot is None:
                raise NotFoundError("FISCAL_CIOT_NOT_FOUND", "CIOT não encontrado.")

            now = datetime.now(timezone.utc)
            protocolo_antt = f"ANTT-{uuid.uuid4().hex[:12].upper()}"
            codigo_ciot = f"CIOT-{uuid.uuid4().hex[:10].upper()}"
            ciot.register(codigo_ciot=codigo_ciot, protocolo_antt=protocolo_antt, now=now)
            await ciot_repo.add(ciot)

            await history_repo.add(
                CiotStatusHistoryEntry.create(
                    ciot_id=ciot.id, status=ciot.status.value, usuario_id=command.actor.user_id,
                    origem="usuario", now=now,
                )
            )
            await event_repo.add(
                FiscalEvent.create(
                    documento_tipo=FiscalEventDocumentType.CIOT, documento_id=ciot.id,
                    tipo_evento=FiscalEventType.RESPOSTA, payload_arquivo_id=uuid.uuid4(),
                    protocolo_externo=protocolo_antt, numero_tentativa=1, resultado=FiscalEventResult.SUCESSO,
                    origem="documents", data_hora_inicio=now, data_hora_fim=now,
                )
            )
            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="ciots", entidade_id=ciot.id,
                acao="TRANSICAO_STATUS", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"status": ciot.status.value},
            )
            await uow.commit()

        return CiotDTO.from_entity(ciot)
