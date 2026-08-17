from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError
from modules.documents.application.dtos.correction_letter_dto import CorrectionLetterDTO
from modules.documents.domain.entities.correction_letter import CorrectionLetter
from modules.documents.domain.value_objects.cte_status import CteStatus
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_correction_letter_repository import (
    SqlAlchemyCorrectionLetterRepository,
)
from modules.documents.infrastructure.persistence.repositories.sqlalchemy_cte_repository import (
    SqlAlchemyCteRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class CreateCorrectionLetterCommand(Command):
    actor: AuthenticatedActor
    cte_id: uuid.UUID
    correction_text: str


class CreateCorrectionLetterHandler(CommandHandler[CreateCorrectionLetterCommand, CorrectionLetterDTO]):
    """Só aceita com CT-e pai `AUTORIZADO` (D282). `numero_sequencial` sempre calculado pela
    aplicação."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: CreateCorrectionLetterCommand) -> CorrectionLetterDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            cte_repo = SqlAlchemyCteRepository(uow.session)
            letter_repo = SqlAlchemyCorrectionLetterRepository(uow.session)

            cte = await cte_repo.get_by_id(command.cte_id)
            if cte is None:
                raise NotFoundError("FISCAL_CTE_NOT_FOUND", "CT-e não encontrado.")
            if cte.status != CteStatus.AUTORIZADO:
                raise ConflictError("FISCAL_CTE_NOT_AUTHORIZED", "CT-e pai precisa estar AUTORIZADO.")

            sequence_number = await letter_repo.next_sequence_number(cte.id)
            now = datetime.now(timezone.utc)
            letter = CorrectionLetter.create(
                cte_id=cte.id, numero_sequencial=sequence_number, texto_correcao=command.correction_text, now=now
            )
            await letter_repo.add(letter)

            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="cartas_correcao",
                entidade_id=letter.id, acao="CRIACAO", ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"cte_id": str(cte.id), "numero_sequencial": letter.numero_sequencial},
            )
            await uow.commit()

        return CorrectionLetterDTO.from_entity(letter)
