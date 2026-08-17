# components/ai-schemas.md — Schemas de IA

Bounded context `ai` (D215). D161: IA nunca decide — todo schema aqui é observacional/consultivo,
nunca um comando que altera outro bounded context diretamente (D311).

## `AIModel` — Modelo de IA

```yaml
AIModel:
  type: object
  description: "D169 — múltiplos modelos ativos simultaneamente é o esperado. D170 — fornecedor_logico nunca é o nome do provedor real."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    name: { type: string, description: "`nome`." }
    type: { type: string, enum: [CLASSIFICACAO, PREDICAO, OTIMIZACAO, VISAO_COMPUTACIONAL, GERACAO_DE_TEXTO], description: "`tipo`." }
    version: { type: string, description: "`versao`." }
    logical_provider: { type: string, enum: [INTERNO, PROVEDOR_EXTERNO], description: "`fornecedor_logico` — D170/D309, nunca OpenAI/Anthropic/Gemini/etc." }
    capability: { type: string, description: "`capacidade`." }
    max_context: { type: integer, description: "`contexto_maximo`." }
    status: { type: string, enum: [EM_TREINAMENTO, ATIVO, DESCONTINUADO] }
  required: [id, name, type, version, logical_provider, capability, status]
```

## `AIInference` — Inferência de IA

```yaml
AIInference:
  type: object
  description: "D172 — auditável: entrada, saída, modelo, versão, duração, custo, origem sempre presentes."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    model_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`modelo_ia_id`." }
    model_version: { type: string, readOnly: true, description: "`modelo_ia_versao` — cópia fixa (D166)." }
    input: { type: object, readOnly: true, description: "`entrada` — ou referência a Storage quando volumosa." }
    output: { type: object, readOnly: true, description: "`saida`." }
    confidence_level: { type: number, readOnly: true, description: "`nivel_confianca` — D168, sempre estatístico, nunca certeza." }
    started_at: { type: string, format: date-time, readOnly: true, description: "`data_hora_inicio`." }
    finished_at: { type: string, format: date-time, readOnly: true, description: "`data_hora_fim`." }
    duration_ms: { type: integer, readOnly: true, description: "`duracao_ms`." }
    cost: { type: string, readOnly: true, description: "`custo` — D267-style, só visível com `ai.inference.view_cost`." }
    attempt_number: { type: integer, readOnly: true, description: "`numero_tentativa`." }
    origin: { type: string, enum: [AUTOMATICO, MANUAL], readOnly: true, description: "`origem`." }
    status: { type: string, enum: [SUCESSO, FALHA, TIMEOUT], readOnly: true }
  required: [id, model_id, model_version, started_at, origin, status]
```

## `AISuggestion` — Sugestão de IA

```yaml
AISuggestion:
  type: object
  description: "D310 — produto derivado da Inferência, nunca fundido com ela. D311 — decisão nunca executa comando operacional diretamente."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    inference_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`inferencia_ia_id` — D167, evidência sempre consultável." }
    category: { type: string, readOnly: true, description: "`categoria` — vocabulário extensível." }
    target_entity_type: { type: string, readOnly: true, description: "`entidade_alvo_tipo`." }
    target_entity_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`entidade_alvo_id`." }
    recommendation: { type: string, readOnly: true, description: "`recomendacao`." }
    justification: { type: string, readOnly: true, description: "`justificativa` — D162, explicabilidade sempre presente." }
    confidence_level: { type: number, readOnly: true, description: "`nivel_confianca`." }
    status: { type: string, enum: [PENDENTE, ACEITA, REJEITADA, IGNORADA, EXPIRADA], readOnly: true }
    decision_user_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`usuario_decisao_id`." }
    decided_at: { type: string, format: date-time, readOnly: true, description: "`data_hora_decisao`." }
  required: [id, inference_id, category, target_entity_type, target_entity_id, recommendation, justification, confidence_level, status]
```

## `AIPrediction` — Predição de IA

```yaml
AIPrediction:
  type: object
  description: "D163/D312 — validade temporal sempre presente. Nunca registra o resultado real (isso é AIFeedback.actual_result, D192)."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    inference_id: { $ref: "../components/schemas.md#/UUID", readOnly: true }
    category: { type: string, readOnly: true, description: "`categoria`." }
    target_entity_type: { type: string, readOnly: true }
    target_entity_id: { $ref: "../components/schemas.md#/UUID", readOnly: true }
    predicted_value: { type: string, readOnly: true, description: "`valor_previsto`." }
    confidence_level: { type: number, readOnly: true }
    valid_until: { type: string, format: date-time, readOnly: true, description: "`data_hora_validade_fim` — horizonte, D163." }
    status: { type: string, enum: [ATUAL, EXPIRADA], readOnly: true }
  required: [id, inference_id, category, target_entity_type, target_entity_id, predicted_value, confidence_level, valid_until, status]
```

## `AIClassification` — Classificação de IA

```yaml
AIClassification:
  type: object
  description: "Enum fechado — Risco/Prioridade/Gravidade. Anomalia é entidade própria (AIAnomaly), nunca confundida (D076, reconciliação já feita no Domain)."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    inference_id: { $ref: "../components/schemas.md#/UUID", readOnly: true }
    classification_type: { type: string, enum: [RISCO, PRIORIDADE, GRAVIDADE], readOnly: true, description: "`tipo_classificacao`." }
    target_entity_type: { type: string, readOnly: true }
    target_entity_id: { $ref: "../components/schemas.md#/UUID", readOnly: true }
    label: { type: string, readOnly: true, description: "`rotulo`." }
    confidence_level: { type: number, readOnly: true }
    created_at: { type: string, format: date-time, readOnly: true }
  required: [id, inference_id, classification_type, target_entity_type, target_entity_id, label, confidence_level, created_at]
```

## `AIAnomaly` — Anomalia Detectada

```yaml
AIAnomaly:
  type: object
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    inference_id: { $ref: "../components/schemas.md#/UUID", readOnly: true }
    source_reading_type: { type: string, readOnly: true, description: "`leitura_origem_tipo` — POSICAO_VEICULO/LEITURA_TELEMETRIA/MEDICAO_PNEU." }
    source_reading_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`leitura_origem_id`." }
    confidence_level: { type: number, readOnly: true }
    status: { type: string, enum: [ABERTA, INVESTIGADA, DESCARTADA] }
  required: [id, inference_id, source_reading_type, source_reading_id, confidence_level, status]
```

## `ComputerVisionReading` — Leitura de Visão Computacional

```yaml
ComputerVisionReading:
  type: object
  description: "D161/D164 — resultado é sempre proposta, nunca aplicado automaticamente."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    inference_id: { $ref: "../components/schemas.md#/UUID", readOnly: true }
    source_file_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`arquivo_origem_id` — D107, nunca blob." }
    reading_type: { type: string, enum: [CANHOTO, AVARIA, MARCA_DE_FOGO, IMPLEMENTO], readOnly: true, description: "`tipo_leitura`." }
    analyzed_region: { type: object, readOnly: true, description: "`regiao_analisada`." }
    extracted_result: { type: object, readOnly: true, description: "`resultado_extraido` — sempre proposta." }
    confidence_level: { type: number, readOnly: true }
    human_review_required: { type: boolean, readOnly: true, description: "`revisao_humana_necessaria`." }
    status: { type: string, enum: [PROCESSADA, CONFIRMADA, REJEITADA] }
    confirmation_user_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`usuario_confirmacao_id` — obrigatório quando revisão humana era necessária e status é terminal." }
  required: [id, inference_id, source_file_id, reading_type, extracted_result, confidence_level, human_review_required, status]
```

## `AIFeedback` — Feedback de IA

```yaml
AIFeedback:
  type: object
  description: "D165 — matéria-prima para evolução dos modelos, nunca altera a decisão original."
  properties:
    id: { $ref: "../components/schemas.md#/UUID" }
    output_type: { type: string, enum: [SUGESTAO, PREDICAO, CLASSIFICACAO, ANOMALIA, LEITURA_VISAO_COMPUTACIONAL], readOnly: true, description: "`saida_ia_tipo`." }
    output_id: { $ref: "../components/schemas.md#/UUID", readOnly: true, description: "`saida_ia_id`." }
    user_id: { $ref: "../components/schemas.md#/UUID", readOnly: true }
    result: { type: string, enum: [ACEITO, REJEITADO, IGNORADO], description: "`resultado`." }
    justification: { type: string, description: "`justificativa`." }
    actual_result: { type: string, description: "`resultado_real` — D192, o que de fato aconteceu depois, base para retreinamento." }
    created_at: { type: string, format: date-time, readOnly: true }
  required: [id, output_type, output_id, user_id, result, created_at]
```

## Como este documento cresce

Nenhum campo identifica o fornecedor real de IA em nenhum schema (D170/D309) — `logical_provider`
é sempre `INTERNO`/`PROVEDOR_EXTERNO`, nunca um nome de produto comercial.
