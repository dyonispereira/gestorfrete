from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class SefazAuthorizationResult:
    approved: bool
    protocolo_sefaz: str
    chave_acesso: str | None = None
    xml_arquivo_id: uuid.UUID | None = None


class SefazGateway(ABC):
    """Lote Fiscal, Parte 2.2 (D397, fechado) — port. Única fronteira entre `documents` e
    "perguntar à SEFAZ se um CT-e foi autorizado". `TRANSMITIDO→AUTORIZADO`/`DENEGADO` sempre foi
    modelado como resposta assíncrona externa (`docs/api/039-cte.md`: "nenhum endpoint do cliente
    dispara essa transição diretamente") — isso continua verdade; o que muda é que agora existe uma
    fronteira real para receber essa resposta, em vez de só um método de teste inacessível por HTTP.

    Nenhuma implementação real de emissão (certificado digital A1/A3, cliente SOAP/REST aos
    webservices da SEFAZ, assinatura XML conforme manual técnico do CT-e) existe nesta fundação —
    só `SandboxSefazGateway` (`infrastructure/gateways`), que simula uma autorização determinística
    para ambiente de desenvolvimento/homologação. Trocar pelo provider real, quando existir e houver
    certificado/credenciais, não toca `domain`/`application` — só o adapter (mesmo padrão de
    `AIModelGateway`, D170/D423)."""

    @abstractmethod
    async def authorize_cte(self, *, cte_id: uuid.UUID) -> SefazAuthorizationResult: ...
