from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class XmlReferenceResponse(BaseModel):
    """D276 — nunca o XML embutido, só a referência ao artefato em Storage. `generated_at` é
    opcional no contrato (`039-cte.md`) — nem todo documento com XML já disponível tem uma coluna de
    timestamp própria capturando exatamente esse momento (ex: MDF-e antes de `ENCERRADO`)."""

    xml_file_id: uuid.UUID
    generated_at: datetime | None
