from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from core.database.unit_of_work import SQLAlchemyUnitOfWork
from modules.freight.application.commands.register_proof_of_delivery import (
    RegisterProofOfDeliveryCommand,
    RegisterProofOfDeliveryHandler,
)
from modules.freight.application.dtos.proof_of_delivery_dto import ProofOfDeliveryDTO
from modules.mobile.domain.entities.digital_signature import DigitalSignature
from modules.mobile.domain.value_objects.signatory_role import SignatoryRole
from modules.mobile.domain.value_objects.signature_document_type import SignatureDocumentType
from modules.mobile.infrastructure.persistence.repositories.sqlalchemy_digital_signature_repository import (
    SqlAlchemyDigitalSignatureRepository,
)
from shared.collaboration.domain.entities.attachment import Attachment
from shared.collaboration.infrastructure.persistence.repositories.sqlalchemy_attachment_repository import (
    SqlAlchemyAttachmentRepository,
)
from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.domain.actor import AuthenticatedActor


@dataclass(frozen=True)
class RegisterMobilePodCommand(Command):
    actor: AuthenticatedActor
    trip_id: uuid.UUID
    delivery_id: uuid.UUID
    photo_file_id: uuid.UUID
    signature_file_id: uuid.UUID
    signatory_role: SignatoryRole
    signatory_name: str | None


class RegisterMobilePodHandler(CommandHandler[RegisterMobilePodCommand, ProofOfDeliveryDTO]):
    """D411 — orquestra três operações já existentes na mesma transação, nenhuma nova: o Canhoto em
    si (`freight`, inalterado), a foto como `Attachment` comum (`shared.collaboration`), e a
    Assinatura Digital (`mobile`). `058-driver-deliveries.md`."""

    async def handle(self, command: RegisterMobilePodCommand) -> ProofOfDeliveryDTO:
        pod_dto = await RegisterProofOfDeliveryHandler().handle(
            RegisterProofOfDeliveryCommand(
                actor=command.actor, trip_id=command.trip_id, delivery_id=command.delivery_id,
                signature_file_id=command.signature_file_id,
            )
        )

        now = datetime.now(timezone.utc)
        async with SQLAlchemyUnitOfWork() as uow:
            attachment_repo = SqlAlchemyAttachmentRepository(uow.session)
            await attachment_repo.create(
                Attachment.create(
                    entidade_tipo="canhotos", entidade_id=pod_dto.id, tipo_anexo="FOTO_CANHOTO",
                    arquivo_id=command.photo_file_id, descricao=None, now=now, created_by=command.actor.user_id,
                )
            )

            signature_repo = SqlAlchemyDigitalSignatureRepository(uow.session)
            await signature_repo.add(
                DigitalSignature.capture(
                    documento_tipo=SignatureDocumentType.CANHOTO, documento_id=pod_dto.id,
                    papel_signatario=command.signatory_role, nome_signatario_informado=command.signatory_name,
                    arquivo_id=command.signature_file_id, captured_at=now, received_at=now,
                )
            )
            await uow.commit()

        return pod_dto
