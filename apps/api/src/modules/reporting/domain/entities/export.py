from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from core.exceptions.base import ConflictError
from modules.reporting.domain.value_objects.export_status import ExportStatus
from shared_kernel.domain.base_entity import BaseEntity


class Export(BaseEntity[uuid.UUID]):
    """`exportacoes_geradas` (D157) — Histórica, assíncrona por padrão (D307). Contexto completo
    (`filtros_utilizados`/`periodo`/`metricas_versoes`) sempre capturado no momento da solicitação,
    nunca aceito como cópia literal do corpo."""

    def __init__(
        self,
        id: uuid.UUID,
        *,
        relatorio_salvo_id: uuid.UUID | None,
        usuario_id: uuid.UUID,
        filtros_utilizados: dict[str, Any],
        periodo: str,
        metricas_versoes: list[dict[str, Any]],
        arquivo_id: uuid.UUID | None,
        mensagem_erro: str | None,
        data_hora_solicitacao: datetime,
        status: ExportStatus,
    ) -> None:
        super().__init__(id)
        self.relatorio_salvo_id = relatorio_salvo_id
        self.usuario_id = usuario_id
        self.filtros_utilizados = filtros_utilizados
        self.periodo = periodo
        self.metricas_versoes = metricas_versoes
        self.arquivo_id = arquivo_id
        self.mensagem_erro = mensagem_erro
        self.data_hora_solicitacao = data_hora_solicitacao
        self.status = status

    @classmethod
    def request(
        cls, *, relatorio_salvo_id: uuid.UUID | None, usuario_id: uuid.UUID, filtros_utilizados: dict[str, Any],
        periodo: str, metricas_versoes: list[dict[str, Any]], now: datetime,
    ) -> "Export":
        return cls(
            id=uuid.uuid4(), relatorio_salvo_id=relatorio_salvo_id, usuario_id=usuario_id,
            filtros_utilizados=filtros_utilizados, periodo=periodo, metricas_versoes=metricas_versoes,
            arquivo_id=None, mensagem_erro=None, data_hora_solicitacao=now, status=ExportStatus.PROCESSANDO,
        )

    def complete(self, *, arquivo_id: uuid.UUID) -> None:
        """D307/D308 — só transiciona a partir de `PROCESSANDO`; `arquivo_id` sempre referência a
        `storage`, nunca o binário."""

        if self.status != ExportStatus.PROCESSANDO:
            raise ConflictError("REPORTING_EXPORT_NOT_PROCESSING", "Exportação não está em processamento.")
        self.arquivo_id = arquivo_id
        self.status = ExportStatus.CONCLUIDA

    def fail(self, *, error_message: str) -> None:
        """Auditoria #7 do usuário — exportação com erro rastreável: `FALHOU` sempre exige uma
        mensagem não vazia."""

        if self.status != ExportStatus.PROCESSANDO:
            raise ConflictError("REPORTING_EXPORT_NOT_PROCESSING", "Exportação não está em processamento.")
        if not error_message:
            raise ValueError("error_message é obrigatório ao marcar uma Exportação como FALHOU.")
        self.mensagem_erro = error_message
        self.status = ExportStatus.FALHOU
