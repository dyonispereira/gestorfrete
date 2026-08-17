from __future__ import annotations

# D322 — `job_type` é validado contra este vocabulário fechado no sentido de nunca aceitar um nome
# livre do cliente (mesmo princípio de `integration.config.type`/`arquivos.origem`, aberto para
# *catalogação*, fechado para *execução* de algo não previsto). Dois tipos ilustrativos bastam para
# provar o mecanismo — nunca inventar integração real com nenhum subsistema pesado (Export/Report
# ficam fora deste lote via D326).
JOB_TYPE_REGISTRY: dict[str, str] = {
    "REPROCESSAMENTO_FILA_SINCRONIZACAO": "Reprocessa itens FALHOU da Fila de Sincronização Mobile.",
    "EXPORTACAO_RELATORIO": "Gera um relatório pesado em background (ilustrativo, sem Report/Export reais neste lote).",
}
