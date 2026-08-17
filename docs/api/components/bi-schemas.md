# components/bi-schemas.md — Schemas de BI (Analytics + Reporting)

Bounded contexts `analytics` (Métrica/Indicador/Snapshot/Cubo) e `reporting` (Dashboard/Filtro/
Relatório/Exportação/Agendamento) — D306: nenhum schema aqui referencia ou altera entidade
operacional, só lê/consulta.

## `Metric`

```yaml
Metric:
  type: object
  description: "D155 — versionada, fórmula histórica nunca sobrescrita."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    name: { type: string, description: "`nome`." }
    formula: { type: string, readOnly: true, description: "`formula` — imutável para a versão atual; mudar gera nova versão." }
    version: { type: integer, readOnly: true, description: "`versao` — nunca decresce." }
    temporal_granularity: { type: string, enum: [DIARIO, SEMANAL, MENSAL, POR_EVENTO], description: "`granularidade_temporal`." }
    dimensional_granularity: { type: string, enum: [VIAGEM, VEICULO, MOTORISTA, CLIENTE, TENANT], description: "`granularidade_dimensional`." }
    unit: { type: string, description: "`unidade` — ex.: km/L, R$, %." }
    data_sources: { type: object, description: "`origem_dados` (JSONB) — bounded contexts/campos que alimentam o cálculo." }
    calculation_periodicity: { type: string, enum: [TEMPO_REAL, INCREMENTAL, DIARIO, MANUAL], description: "`periodicidade_calculo`." }
    status: { type: string, enum: [ATIVA, DESCONTINUADA] }
  required: [id, name, formula, version, temporal_granularity, dimensional_granularity, unit, calculation_periodicity, status]
```

## `ConsolidatedIndicator`

```yaml
ConsolidatedIndicator:
  type: object
  description: "Todo campo readOnly — nunca aceita fórmula/valor digitado (D156)."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    metric_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`metrica_id`." }
    metric_version: { type: integer, readOnly: true, description: "`metrica_versao` — cópia fixa, nunca a fórmula em si." }
    dimension_type: { type: string, readOnly: true, description: "`dimensao_tipo`." }
    dimension_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`dimensao_id`." }
    reference_period: { type: string, readOnly: true, description: "`periodo_referencia` — ex.: \"2026-06\"." }
    value: { type: string, readOnly: true, description: "`valor`." }
    calculated_at: { type: string, format: date-time, readOnly: true, description: "`data_hora_calculo`." }
    status: { type: string, enum: [VALIDO, RECALCULADO, SNAPSHOTADO], readOnly: true }
  required: [id, metric_id, metric_version, dimension_type, dimension_id, reference_period, value, calculated_at, status]
```

## `AnalyticalSnapshot`

```yaml
AnalyticalSnapshot:
  type: object
  description: "Imutável após CONSOLIDADO (D151)."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    reference_period: { type: string, description: "`periodo_referencia`." }
    consolidated_at: { type: string, format: date-time, readOnly: true, description: "`data_hora_consolidacao`." }
    processing_origin: { type: string, enum: [AUTOMATICO, MANUAL], readOnly: true, description: "`origem_processamento`." }
    user_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`usuario_id` — obrigatório quando MANUAL." }
    participating_metrics:
      type: array
      readOnly: true
      description: "D160 — lista de {metric_id, metric_version}, nunca um fechamento opaco."
      items:
        type: object
        properties:
          metric_id: { $ref: "../components/schemas.md#/UUID" }
          metric_version: { type: integer }
    indicator_ids:
      type: array
      readOnly: true
      items: { $ref: "../components/schemas.md#/UUID" }
    status: { type: string, enum: [EM_PROCESSAMENTO, CONSOLIDADO, INVALIDO], readOnly: true }
  required: [id, reference_period, processing_origin, status]
```

## `AnalyticsCube`

```yaml
AnalyticsCube:
  type: object
  description: "D291-style — só a definição estrutural (dimensões/medidas), nunca dado materializado nem infraestrutura de execução."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    name: { type: string, description: "`nome` — único por tenant." }
    dimensions: { type: array, items: { type: string }, description: "`dimensoes` — ex.: [\"Tempo\", \"Veículo\", \"Motorista\"]." }
    metric_ids: { type: array, items: { $ref: "../components/schemas.md#/UUID" }, description: "`metricas_ids` — ao menos uma." }
    status: { type: string, enum: [ATIVO, INATIVO] }
  required: [id, name, dimensions, metric_ids, status]
```

## `Dashboard`

```yaml
Dashboard:
  type: object
  description: "D152 — nunca guarda valor de KPI, só configuração/referência."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    user_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`usuario_id`." }
    name: { type: string, description: "`nome` — único por usuário." }
    layout: { type: object, description: "`layout` — posição/tamanho de cada widget." }
    widgets:
      type: array
      description: "`widgets` — cada item referencia metric_id/indicator_id, nunca copia valor (D152)."
      items:
        type: object
        properties:
          metric_id: { $ref: "../components/schemas.md#/UUID" }
          indicator_id: { $ref: "../components/schemas.md#/UUID" }
          visualization_type: { type: string }
    filters: { type: object, description: "`filtros`." }
    sharing: { type: string, enum: [PRIVADO, COMPARTILHADO_COM_GRUPO, COMPARTILHADO_COM_PAPEL], description: "`permissoes_compartilhamento` — intenção; autorização real ainda é RBAC (D060)." }
    preferences: { type: object, description: "`preferencias` — nunca um atributo operacional." }
    status: { type: string, enum: [ATIVO, ARQUIVADO] }
    audit: { $ref: "../components/schemas.md#/AuditMetadata" }
  required: [id, user_id, name, layout, widgets, status, audit]
```

## `SavedFilter`

```yaml
SavedFilter:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    user_id: { $ref: "../components/schemas.md#/UUID", readOnly: true }
    name: { type: string, description: "único por usuário." }
    criteria: { type: object, description: "`criterios` — nunca guarda o resultado, só o critério." }
    status: { type: string, enum: [ATIVO, ARQUIVADO] }
  required: [id, user_id, name, criteria, status]
```

## `SavedReport`

```yaml
SavedReport:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    user_id: { $ref: "../components/schemas.md#/UUID", readOnly: true }
    name: { type: string, description: "único por usuário." }
    metric_ids: { type: array, items: { $ref: "../components/schemas.md#/UUID" } }
    filters: { type: object }
    output_format: { type: string, enum: [PDF, EXCEL, CSV], description: "`formato_saida`." }
    status: { type: string, enum: [ATIVO, ARQUIVADO] }
  required: [id, user_id, name, metric_ids, output_format, status]
```

## `Export`

```yaml
Export:
  type: object
  description: "D157 — contexto completo sempre presente. D307/D308 — assíncrona, arquivo em Storage."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    saved_report_id: { $ref: "../components/schemas.md#/UUID", description: "`relatorio_salvo_id` — opcional, exportação avulsa de Dashboard não exige Relatório Salvo." }
    user_id: { $ref: "../components/schemas.md#/UUID", readOnly: true }
    filters_used: { type: object, readOnly: true, description: "`filtros_utilizados` — capturado no momento da solicitação." }
    period: { type: string, readOnly: true, description: "`periodo`." }
    metric_versions:
      type: array
      readOnly: true
      description: "`metricas_versoes` — [{metric_id, version}], mesma disciplina de Snapshot (D160)."
      items:
        type: object
        properties:
          metric_id: { $ref: "../components/schemas.md#/UUID" }
          version: { type: integer }
    file_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`arquivo_id` — D107/D308, obrigatório quando CONCLUIDA." }
    error_message: { type: string, readOnly: true, description: "`mensagem_erro` — preenchido quando FALHOU." }
    requested_at: { type: string, format: date-time, readOnly: true, description: "`data_hora_solicitacao`." }
    status: { type: string, enum: [PROCESSANDO, CONCLUIDA, FALHOU], readOnly: true }
  required: [id, user_id, filters_used, period, metric_versions, requested_at, status]
```

## `ScheduledUpdate`

```yaml
ScheduledUpdate:
  type: object
  description: "D159 — nunca calcula, só solicita/define política."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    metric_id: { $ref: "../components/schemas.md#/UUID", description: "`metrica_id` — um dos dois (metric_id/cube_id) é obrigatório." }
    cube_id: { $ref: "../components/schemas.md#/UUID", description: "`cubo_analitico_id`." }
    mode: { type: string, enum: [TEMPO_REAL, INCREMENTAL, DIARIO, MANUAL], description: "`modo`." }
    status: { type: string, enum: [ATIVO, INATIVO] }
  required: [id, mode, status]
```

## Como este documento cresce

Nenhum campo de infraestrutura de execução (ClickHouse/BigQuery/Power BI/DuckDB) é adicionado aqui
— `AnalyticsCube` é só a definição estrutural (D065-lote instrução), a implementação física do
cubo é decisão de Backend, nunca exposta neste contrato.
