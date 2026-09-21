from __future__ import annotations

import time
import uuid

from modules.documents.domain.gateways.sefaz_gateway import SefazAuthorizationResult, SefazGateway


class SandboxSefazGateway(SefazGateway):
    """Simula sempre `AUTORIZADO` — não tenta simular rejeições/indisponibilidade real da SEFAZ
    (fora de escopo desta fundação), só o suficiente para destravar o caminho Viagem→CT-e→
    Autorizado→Fatura em desenvolvimento/homologação sem certificado digital real.
    `chave_acesso`/`protocolo_sefaz` têm o formato de uma resposta real (44 dígitos numéricos para
    a chave, protocolo alfanumérico), mas nunca serão validáveis contra a SEFAZ de verdade — o
    prefixo `SANDBOX-` no protocolo deixa isso explícito em qualquer tela/log que os exiba."""

    async def authorize_cte(self, *, cte_id: uuid.UUID) -> SefazAuthorizationResult:
        protocolo = f"SANDBOX-{uuid.uuid4().hex[:20].upper()}"
        chave_acesso = f"{int(time.time() * 1000):013d}{uuid.uuid4().int:031d}"[:44]
        return SefazAuthorizationResult(
            approved=True, protocolo_sefaz=protocolo, chave_acesso=chave_acesso, xml_arquivo_id=uuid.uuid4()
        )
