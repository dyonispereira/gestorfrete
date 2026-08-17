from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.audit.audit_logger import AuditLogger
from core.database.unit_of_work import SQLAlchemyUnitOfWork
from core.exceptions.base import ConflictError, NotFoundError
from modules.freight.application.dtos.proof_of_delivery_dto import ProofOfDeliveryDTO
from modules.freight.domain.entities.proof_of_delivery import ProofOfDelivery
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_delivery_repository import (
    SqlAlchemyDeliveryRepository,
)
from modules.freight.infrastructure.persistence.repositories.sqlalchemy_proof_of_delivery_repository import (
    SqlAlchemyProofOfDeliveryRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class RegisterProofOfDeliveryCommand(Command):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    delivery_id: uuid.UUID
    signature_file_id: uuid.UUID | None


class RegisterProofOfDeliveryHandler(CommandHandler[RegisterProofOfDeliveryCommand, ProofOfDeliveryDTO]):
    """`POST /viagens/{id}/entregas/{entregaId}/canhoto` — D373. Publica `CanhotoRegistrado`
    (consumido por `financial`, fora do controle direto deste handler, D375-style: sem consumidor
    real ainda)."""

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._audit = audit_logger or AuditLogger()

    async def handle(self, command: RegisterProofOfDeliveryCommand) -> ProofOfDeliveryDTO:
        async with SQLAlchemyUnitOfWork() as uow:
            delivery_repo = SqlAlchemyDeliveryRepository(uow.session)
            pod_repo = SqlAlchemyProofOfDeliveryRepository(uow.session)

            delivery = await delivery_repo.get_by_id(command.delivery_id)
            if delivery is None or delivery.viagem_id != command.trip_id:
                raise NotFoundError("FREIGHT_DELIVERY_NOT_FOUND", "Entrega não encontrada.")

            if await pod_repo.exists_for_delivery(command.delivery_id):
                raise ConflictError("FREIGHT_POD_ALREADY_REGISTERED", "Canhoto já registrado para esta Entrega.")

            pod = ProofOfDelivery.create(
                entrega_id=command.delivery_id,
                signature_file_id=command.signature_file_id,
                now=datetime.now(timezone.utc),
            )
            await pod_repo.create(pod)

            await self._audit.record(
                uow.session,
                tenant_id=command.actor.tenant_id,
                entidade_tipo="canhotos",
                entidade_id=pod.id,
                acao="CRIACAO",
                ator_id=command.actor.user_id,
                ator_nome_snapshot=str(command.actor.user_id),
                dados_depois={"entrega_id": str(pod.entrega_id)},
            )

            await uow.commit()

        return ProofOfDeliveryDTO.from_entity(pod)
