from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import NotFoundError, ValidationError
from modules.fleet.application.availability_projector import VehicleAvailabilityProjector
from modules.maintenance.application.dtos.checklist_dto import ChecklistDTO
from modules.maintenance.domain.entities.checklist import Checklist
from modules.maintenance.domain.entities.checklist_status_history_entry import ChecklistStatusHistoryEntry
from modules.maintenance.domain.entities.ordem_servico import OrdemServico
from modules.maintenance.domain.entities.ordem_servico_status_history_entry import OrdemServicoStatusHistoryEntry
from modules.maintenance.domain.value_objects.checklist_type import ChecklistType
from modules.maintenance.domain.value_objects.ordem_servico_origem_abertura import OrdemServicoOrigemAbertura
from modules.maintenance.domain.value_objects.ordem_servico_tipo import OrdemServicoTipo
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_checklist_repository import (
    SqlAlchemyChecklistRepository,
)
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_checklist_status_history_repository import (
    SqlAlchemyChecklistStatusHistoryRepository,
)
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_ordem_servico_repository import (
    SqlAlchemyOrdemServicoRepository,
)
from modules.maintenance.infrastructure.persistence.repositories.sqlalchemy_ordem_servico_status_history_repository import (
    SqlAlchemyOrdemServicoStatusHistoryRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class RejectChecklistCommand(Command):
    actor: AuthenticatedActor
    checklist_id: uuid.UUID
    observacao: str


class RejectChecklistHandler(CommandHandler[RejectChecklistCommand, ChecklistDTO]):
    """`CONCLUIDO→REPROVADO`. Um Checklist `Reprovado` nunca é reaberto — este comando sempre cria
    um novo Checklist `Pendente` (mesmo tipo/referência/veículo/motorista), referenciando o
    reprovado (`007-CHECKLIST.md`). Quando a referência é uma Viagem, ela permanece em
    `AGUARDANDO_CHECKLIST` (nunca recua nem avança sozinha) — nenhuma chamada a `freight` é
    necessária aqui, diferente de `approve_checklist`. Quando `TIPO=OFICINA`, abre automaticamente
    uma Ordem de Serviço corretiva no mesmo veículo (`origem_abertura=CHECKLIST_REPROVADO`, valor
    já reservado no enum antes desta Ordem de Serviço existir) — mesma bounded context
    (`maintenance`→`maintenance`), sem cruzar para `freight`. Essa OS corretiva bloqueia a
    disponibilidade do veículo em `fleet` (`EM_MANUTENCAO`) do mesmo jeito que `create_ordem_
    servico.py` faz para OS abertas manualmente — chamada cross-module após o commit."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: RejectChecklistCommand) -> ChecklistDTO:
        if not command.observacao or not command.observacao.strip():
            raise ValidationError(
                "MAINTENANCE_CHECKLIST_OBSERVACAO_REQUIRED", "observacao é obrigatória para reprovar."
            )

        async with SQLAlchemyUnitOfWork() as uow:
            checklist_repo = SqlAlchemyChecklistRepository(uow.session)
            history_repo = SqlAlchemyChecklistStatusHistoryRepository(uow.session)

            checklist = await checklist_repo.get_by_id(command.checklist_id)
            if checklist is None:
                raise NotFoundError("MAINTENANCE_CHECKLIST_NOT_FOUND", "Checklist não encontrado.")

            now = datetime.now(timezone.utc)
            checklist.reject(now=now)
            await checklist_repo.add(checklist)
            await history_repo.add(
                ChecklistStatusHistoryEntry.create(
                    checklist_id=checklist.id, status=checklist.status.value, usuario_id=command.actor.user_id,
                    origem="usuario", now=now, observacao=command.observacao,
                )
            )

            novo_checklist = Checklist.create(
                tipo=checklist.tipo, referencia_tipo=checklist.referencia_tipo, referencia_id=checklist.referencia_id,
                veiculo_tracionador_id=checklist.veiculo_tracionador_id, motorista_id=checklist.motorista_id,
                now=now, checklist_reprovado_id=checklist.id,
            )
            await checklist_repo.add(novo_checklist)
            await history_repo.add(
                ChecklistStatusHistoryEntry.create(
                    checklist_id=novo_checklist.id, status=novo_checklist.status.value, usuario_id=None,
                    origem="sistema", now=now,
                    observacao=f"Criado automaticamente após reprovação do Checklist {checklist.codigo}.",
                )
            )

            corrective_work_order_id: uuid.UUID | None = None
            if checklist.tipo is ChecklistType.OFICINA:
                os_repo = SqlAlchemyOrdemServicoRepository(uow.session)
                os_history_repo = SqlAlchemyOrdemServicoStatusHistoryRepository(uow.session)
                ordem_corretiva = OrdemServico.create(
                    veiculo_tracionador_id=checklist.veiculo_tracionador_id, composicao_veicular_id=None,
                    fornecedor_executor_id=None, tipo=OrdemServicoTipo.CORRETIVA,
                    origem_abertura=OrdemServicoOrigemAbertura.CHECKLIST_REPROVADO,
                    descricao_problema=f"Aberta automaticamente pela reprovação do Checklist {checklist.codigo}: {command.observacao}",
                    hodometro_abertura_km=None, criado_por=None, now=now,
                )
                await os_repo.add(ordem_corretiva)
                await os_history_repo.add(
                    OrdemServicoStatusHistoryEntry.create(
                        ordem_servico_id=ordem_corretiva.id, status=ordem_corretiva.status.value, usuario_id=None,
                        origem="sistema", now=now,
                        observacao=f"Aberta automaticamente pela reprovação do Checklist {checklist.codigo}.",
                    )
                )
                corrective_work_order_id = ordem_corretiva.id

            dados_depois: dict[str, object] = {
                "status": checklist.status.value, "novo_checklist_id": str(novo_checklist.id),
            }
            if corrective_work_order_id is not None:
                dados_depois["ordem_servico_corretiva_id"] = str(corrective_work_order_id)
            await self._audit.record(
                uow.session, tenant_id=command.actor.tenant_id, entidade_tipo="checklists", entidade_id=checklist.id,
                acao="TRANSICAO_STATUS", ator_id=command.actor.user_id, ator_nome_snapshot=str(command.actor.user_id),
                dados_depois=dados_depois, motivo=command.observacao,
            )
            await uow.commit()

        if corrective_work_order_id is not None:
            await VehicleAvailabilityProjector().apply_service_order_opened(
                vehicle_id=checklist.veiculo_tracionador_id, at=now
            )

        return ChecklistDTO.from_entity(checklist)
