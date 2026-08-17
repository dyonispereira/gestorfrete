# docs/backend/ai — Sprint 11, Lote 12 (IA)

Bounded context `ai` — Modelo de IA, Inferência de IA, Sugestão de IA, Predição de IA, Classificação
de IA, Anomalia Detectada, Leitura por Visão Computacional, Feedback de IA. 8 entidades,
`docs/api/071-077.md` + `components/ai-schemas.md`, congelados desde a Sprint 10 (D306–D313).

| Documento | Cobre |
|---|---|
| [`AI_IMPLEMENTATION.md`](./AI_IMPLEMENTATION.md) | As 8 entidades, `AIModelGateway`/`FakeAIModelGateway` (D423), `AIInferenceEngine` (D424), status de Predição recalculado na leitura (D425) |

## D161/D164 — princípio central, mecanizado nesta lote

`ai` **nunca** decide nem altera operação diretamente — só sugere, prevê, classifica ou sinaliza. A
decisão final e a execução continuam sempre com o usuário ou com o bounded context operacional dono
da regra. D426 torna isso um contrato `import-linter` módulo-inteiro-contra-módulo-inteiro (mesmo
formato de D405/D421): todo módulo operacional é proibido de importar `modules.ai`, em qualquer
camada. `AIInferenceEngine` (D424) nunca escreve em `freight`/`fleet`/`financial`/`maintenance` — as
referências `entidade_alvo_tipo`/`entidade_alvo_id` são sempre polimórficas sem FK física, exatamente
como a DDL congelada as modela.

## D170 — desacoplado do fornecedor, mecanizado nesta lote

`domain.gateways.AIModelGateway` é um port `ABC`; `infrastructure.gateways.FakeAIModelGateway` é a
única implementação — determinística, sem chamada de rede, sem nenhuma dependência de SDK de
provedor real (OpenAI/Anthropic/Gemini/Azure/Ollama). Integração real fica para uma futura sprint de
integrações (D423).

## Auditorias obrigatórias (pedidas explicitamente pelo usuário)

1. IA nunca altera domínio operacional diretamente — Viagem/Manutenção/Financeiro/Frota permanecem
   inalterados depois de criar Sugestão/Predição/Classificação, sem um comando explícito do bounded
   context proprietário.
2. Modelo e versão congelados por Inferência — mudar a versão ativa do modelo não altera
   `modelo_ia_id`/`modelo_ia_versao` de uma Inferência já executada.
3. Confiança não vira decisão — mesmo uma Inferência de alta confiança nunca executa comando
   operacional automaticamente.
4. Visão Computacional com revisão humana — `revisao_humana_necessaria = true` exige
   `usuario_confirmacao_id` em todo estado terminal (`ck_leituras_visao_computacional_confirmacao_
   humana`), reforçado a nível de banco, não só de aplicação.
5. Evidência preservada — `arquivo_origem_id` nunca é substituído por binário/base64; a Inferência
   nunca troca o Arquivo original.
6. Feedback e resultado real registrados sem modificar retroativamente a Predição/Inferência
   original.
7. Autorização por campo de custo — `ai.inference.view_cost` controla só `cost`, nunca a Inferência
   inteira.
8. D170 — fornecedor agnóstico — nenhum import de SDK de provedor real em `modules.ai`.
9. D426 — novo contrato `import-linter`.
10. Nenhum evento de IA inventado — `EVENT_MAP.md` não ganha nenhum evento novo nesta lote.

## Critério de Definição de Pronto (D352)

Migration real, Repository testado, Application testado, E2E via HTTP, tenant isolation + auditoria
— aplicado às 8 entidades.

## Decisões

D423–D426 — ver [`../../product/DECISIONS.md`](../../product/DECISIONS.md).

## Achados deste lote (Sprint 11, Lote 12)

- **As 10 auditorias pedidas foram verificadas por teste real**, não só por leitura de código —
  `tests/integration/test_ia_flow.py` (14 testes, todos verdes contra Postgres real). Auditorias 8
  (fornecedor agnóstico) e 10 (nenhum evento inventado) são testes puramente estruturais (AST/
  filesystem, sem banco) — a primeira quase deu falso positivo: um grep textual ingênuo apontava
  "openai"/"anthropic"/"ollama" nos próprios docstrings do código (que citam esses nomes só para
  explicar o que NUNCA deve ser importado) — corrigido para analisar `import`/`from` reais via
  `ast.walk`, imune a prosa explicativa.
- **Achado físico real, não previsto na DDL em prosa**: `sugestoes_ia`/`predicoes_ia`/
  `classificacoes_ia`/`anomalias_detectadas`/`leituras_visao_computacional.inferencia_ia_id` são
  documentadas como `REFERENCES inferencias_ia(id)` em `relational/012-ia.md`, mas isso é
  fisicamente impossível: `inferencias_ia` é particionada por `data_hora_inicio` (D201) com PK
  composta `(id, data_hora_inicio)`, e o Postgres exige que TODA constraint `UNIQUE` de uma tabela
  particionada — não só a PK — inclua a coluna de partição (`FeatureNotSupportedError` real,
  confirmado tentando `UNIQUE(id)` isolado antes de descobrir isso). Resolvido removendo a FK
  física das 5 tabelas dependentes (mesma coluna UUID, sem `REFERENCES`) — integridade garantida
  pela aplicação (`AIInferenceEngine` sempre cria a Inferência antes da saída, na mesma transação),
  nunca pelo banco. Aplicação direta de D202 ("resolvido no modelo físico sem mudar a identidade
  funcional da entidade").
- **D421/D405 têm agora um terceiro par**: D426 verificado manualmente via `lint-imports` (injeção
  deliberada de `from modules.ai.domain.entities.ai_model import AIModel` em `freight/domain/
  entities/trip.py`) — contrato reportou `BROKEN` imediatamente (`11 kept, 1 broken`), revertido em
  seguida, `12 kept, 0 broken` de novo.
- **`AIInferenceEngine` prova D161/D164 mecanicamente**: nenhum método do Engine escreve em
  `freight`/`fleet`/`financial`/`maintenance` — testado criando uma Viagem e um Veículo reais,
  gerando uma Sugestão referenciando cada um, aceitando a Sugestão, e comparando o JSON completo
  da Viagem/Veículo byte-a-byte antes e depois (nunca mudou um único campo).
- **`ck_leituras_visao_computacional_confirmacao_humana` provado nos dois níveis**: a Application
  recusa a transição antes de chegar ao banco (`409 AI_CV_READING_INVALID_TRANSITION`); um teste
  separado contorna a Application via SQL bruto (`UPDATE` direto tentando `status=CONFIRMADA` com
  `usuario_confirmacao_id=NULL` numa leitura que exige revisão humana) e confirma que o Postgres
  rejeita com `IntegrityError` mesmo assim — a constraint física é a segunda linha de defesa real,
  não decorativa.
- **Suite completa**: 141 testes de integração verdes (127 herdados do Lote 11 + 14 novos), 2
  deselected apenas Redis/RabbitMQ (pendência de infraestrutura pré-existente desde o Lote 1, não
  afetada por este lote). Nenhuma regressão cross-lote.

## Como esta pasta cresce

Depois deste lote, por instrução explícita do usuário: **Backend Freeze** (banco vazio → Alembic
HEAD, auditoria OpenAPI↔rotas, RBAC↔endpoints, Redis+RabbitMQ reais, suíte completa), só então
Frontend.
