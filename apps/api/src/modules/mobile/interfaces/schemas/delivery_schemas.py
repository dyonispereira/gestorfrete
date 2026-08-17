from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class MobilePodRequest(BaseModel):
    """`058-driver-deliveries.md` — diferente de `RegisterProofOfDeliveryRequest` (`freight`, só
    `signature_file_id`): aqui `photo_file_id`/`signatory_role` também são exigidos (D411)."""

    model_config = ConfigDict(extra="ignore")

    photo_file_id: uuid.UUID
    signature_file_id: uuid.UUID
    signatory_role: str
    signatory_name: str | None = None
