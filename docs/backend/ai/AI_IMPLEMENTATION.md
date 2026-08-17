# AI_IMPLEMENTATION.md — Modelo/Inferência/Sugestão/Predição/Classificação/Anomalia/Visão/Feedback (071-077)

Bounded context `ai` (`apps/api/src/modules/ai/`).

## `AIModelGateway`/`FakeAIModelGateway` — mecanização de D170 (D423)

Port `ABC` em `domain/gateways/ai_model_gateway.py`: `run(*, model: AIModel, input: dict) ->
AIModelGatewayResult` (`output: dict`, `confidence_level: Decimal`, `cost: Decimal | None`). A única
implementação, `infrastructure/gateways/fake_ai_model_gateway.py`, é determinística — deriva
`output`/`confidence_level` de um hash SHA-256 do `input` serializado (mesmo `input` sempre produz o
mesmo resultado, útil para teste) — `cost` só é preenchido quando `model.fornecedor_logico ==
PROVEDOR_EXTERNO` (modelo interno nunca tem custo variável, conforme a DDL). Nenhuma linha de código
em `domain`/`application`/`infrastructure` deste módulo importa um SDK de provedor real — verificado
por teste (audit 8).

## Modelo de IA (071) — Reference Data, versão nunca sobrescrita

CRUD administrativo restrito (`ai.model.create`/`.edit`, criticidade Alta). `POST` sempre cria uma
linha nova — não existe "nova versão de um Modelo existente" como transformação (diferente de
`Metric.new_version`, Lote 11): trocar a versão é simplesmente `POST` de novo com o mesmo `nome` e
`versao` diferente; `uq_modelos_ia_nome_versao` impede duplicidade. `PATCH` é parcial (`capability`/
`max_context`/`status` apenas) — `name`/`type`/`version`/`logical_provider` nunca editáveis. Sem
`DELETE` — descontinuação via `PATCH status=DESCONTINUADO`.

## Inferência de IA (072) — técnico, nunca alcançável por HTTP em escrita

`inferencias_ia` — Time Series/Alto volume, particionada mensalmente por `data_hora_inicio` (mesmo
padrão de `eventos_fiscais`, Lote 8), com uma única partição `DEFAULT`. `AIInferenceEngine` (D424,
mesma família de `TripInternalTransitions`/`AnalyticsCalculationEngine`) é o único lugar que cria
uma Inferência: chama `AIModelGateway.run(model, input)`, grava `modelo_ia_id`+`modelo_ia_versao`
(cópia fixa do `Metric.versao` do Modelo no momento da execução, D166/D169), `data_hora_inicio`/
`data_hora_fim` (síncrono, os dois no mesmo instante de execução do fake adapter), `duracao_ms`
(coluna `GENERATED ALWAYS AS (...) STORED`, nunca calculada em Python — lida de volta do banco após
`flush`+`refresh`, mesmo padrão de `FiscalEvent.duracao_ms`/D382), e cria exatamente uma saída de
negócio na mesma transação. `GET /ai/inferences` expõe `cost` só com `ai.inference.view_cost`
(D267-style, mesmo padrão de `financial.trip_*_value.view`/Lote 7 e `ConsolidatedIndicatorResponse`/
Lote 11) — sem a permissão, `cost` é sempre `null`, nunca omitido do schema.

## Sugestão de IA (073) — decisão sempre humana

`POST /ai/suggestions/{id}/commands/accept|reject|ignore` — as três únicas transições reais a partir
de `PENDENTE`; qualquer uma fora desse estado é `409 AI_SUGGESTION_INVALID_TRANSITION`. **D311,
literal**: `accept` só grava `status=ACEITA`/`decision_user_id`/`decided_at` — nunca chama nenhum
comando de `freight`/`fleet`/`financial`/`maintenance`. `EXPIRADA` é um estado real do enum sem
gatilho automático nesta fundação (nenhum job agendado existe) — documentado, não construído.

## Predição de IA (074) — status recalculado na leitura (D425)

`predicoes_ia.status` físico nunca é atualizado por um job (não existe nesta fundação) — `Get
PredictionHandler`/`ListPredictionsHandler` sempre recalculam o status efetivo comparando `now()`
contra `data_hora_validade_fim`, nunca confiam cegamente na coluna gravada. `include_expired=false`
(padrão) só lista `ATUAL` efetivo; `true` inclui `EXPIRADA` explicitamente. Sem `POST`/`PATCH`/
`DELETE` — nasce só via `AIInferenceEngine`.

## Classificação de IA (075) — rótulo pontual, nunca regra automática

Só leitura via HTTP — `ai.classification.view`. Nenhuma ação em outro bounded context é disparada
pela leitura da Classificação; se um Gestor decide agir, é sempre um comando explícito no módulo
correspondente.

## Anomalia Detectada (075) — evento de fluxo contínuo, distinta de Classificação

`POST /ai/anomalies/{id}/commands/review` — única transição real, `ABERTA → INVESTIGADA` ou
`ABERTA → DESCARTADA`; fora de `ABERTA` é `409 AI_ANOMALY_INVALID_TRANSITION`. `leitura_origem_tipo`/
`leitura_origem_id` nunca são alteradas nem a leitura de origem é tocada (D164).

## Leitura por Visão Computacional (076) — confirmação sempre humana, reforçada em dois níveis

`ck_leituras_visao_computacional_confirmacao_humana` (DDL): todo estado terminal (`CONFIRMADA`/
`REJEITADA`) que exigia revisão humana precisa de `usuario_confirmacao_id` preenchido — reforçado
pela Application (`confirm`/`reject` só aplicáveis quando `revisao_humana_necessaria=true` e
`status=PROCESSADA`, senão `409 AI_CV_READING_INVALID_TRANSITION`) **e** pela constraint física do
Postgres, provada por teste que tenta violá-la diretamente via SQL bruto, contornando a Application
(audit 4). `arquivo_origem_id` é sempre referência a `storage` (D107) — nunca binário inline; a
Inferência nunca substitui o Arquivo original, só propõe um `resultado_extraido` (JSONB).

## Feedback de IA (077) — nunca reabre a decisão original

`POST /ai/feedback` valida que `output_id` referencia uma saída de IA real (dispatch por
`output_type` → repositório correspondente, `404` se não existir) — polimórfico sobre as 5 saídas.
`PATCH /ai/feedback/{id}` só edita `actual_result` (D192) — `result`/`justification` permanecem
imutáveis após criado. Registrar Feedback nunca reabre/altera `AISuggestion.status`/
`decision_user_id` nem qualquer campo da saída avaliada ou da Inferência original (audit 6).

## Nenhum Domain Event novo (audit 10)

`EVENT_MAP.md` não tem nenhum evento de `ai` catalogado e nenhum `flows/0NN-IA.md` existe — mesmo
achado já registrado no OpenAPI (`073-ai-suggestions.md`). Esta lote não cria nenhum arquivo em
`domain/events/` além do `__init__.py` vazio já existente — se a implementação demonstrar
necessidade real de um evento, isso é achado a registrar, nunca inventado silenciosamente.

## Auditorias deste lote (candidatas, numeradas conforme o pedido do usuário)

Ver a lista completa em [`README.md`](./README.md#auditorias-obrigatórias-pedidas-explicitamente-pelo-usuário).

## Achados deste lote

- **Gap físico entre a DDL congelada e o Postgres real**: `relational/012-ia.md` declara
  `inferencia_ia_id UUID NOT NULL REFERENCES inferencias_ia(id)` nas 5 tabelas de saída de IA, mas
  `inferencias_ia` é particionada por `data_hora_inicio` (D201) — Postgres exige que toda constraint
  `UNIQUE` de uma tabela particionada inclua a coluna de partição, então um `UNIQUE(id)` isolado
  (necessário para a FK single-column funcionar) é fisicamente rejeitado
  (`FeatureNotSupportedError`, testado e confirmado contra o Postgres real antes da correção).
  Resolvido: `inferencia_ia_id` continua a mesma coluna UUID documentada, só sem `REFERENCES` físico
  — integridade garantida pela aplicação (`AIInferenceEngine` sempre grava a Inferência antes da
  saída de negócio, na mesma transação/commit). D202 já previa exatamente este tipo de resolução.
- **`AIModelGateway`/`FakeAIModelGateway` (D423) provados end-to-end**: `run_computer_vision` usa o
  `output` bruto do gateway como `resultado_extraido` diretamente — nenhuma transformação adicional
  — e `revisao_humana_necessaria` é derivado de um limiar fixo (`80.00`) contra o `confidence_level`
  determinístico do gateway. O teste de auditoria 4 precisou tentar várias `input` diferentes (loop
  de até 60 seeds) até encontrar uma cujo hash produzisse confiança abaixo do limiar — confirma que
  o determinismo funciona (mesma seed sempre produz a mesma confiança) sem exigir um adapter
  configurável para testes.
- **Nenhum evento de IA foi necessário nesta lote** — `AIInferenceEngine`/os 9 comandos HTTP
  (accept/reject/ignore de Sugestão, review de Anomalia, confirm/reject de Leitura de Visão,
  create/update de Feedback) nunca precisaram publicar um Domain Event para completar seu próprio
  fluxo — cada saída de IA é lida diretamente via `GET`, nunca via projeção assíncrona. Confirma a
  previsão do kickoff: não havia necessidade real, então nada foi inventado (audit 10).
- **Auditoria 8 quase deu falso positivo**: uma primeira versão do teste fazia grep textual por
  "openai"/"anthropic"/"ollama" em todo `.py` de `modules/ai` — e encontrou essas strings nos
  próprios docstrings do código-fonte (que as citam propositalmente para explicar D170: "nunca
  importa OpenAI/Anthropic/..."). Corrigido para usar `ast.walk` e inspecionar apenas nós
  `Import`/`ImportFrom` reais — a documentação explicativa deixou de ser confundida com uso real.
