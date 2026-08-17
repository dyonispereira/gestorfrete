# docs/backend/bi — Sprint 11, Lote 11 (BI)

Bounded contexts `analytics` (Métrica/Indicador Consolidado/Snapshot Analítico/Cubo Analítico) e
`reporting` (Dashboard/Filtro Favorito/Relatório Salvo/Exportação/Agendamento de Atualização) — 9
entidades, `docs/api/062-070.md` + `components/bi-schemas.md`, congelados desde a Sprint 10.

| Documento | Cobre |
|---|---|
| [`ANALYTICS_IMPLEMENTATION.md`](./ANALYTICS_IMPLEMENTATION.md) | `analytics` — Métrica (D419, versionamento), Indicador Consolidado, Snapshot Analítico (D151), Cubo Analítico, `AnalyticsCalculationEngine` (D420) |
| [`REPORTING_IMPLEMENTATION.md`](./REPORTING_IMPLEMENTATION.md) | `reporting` — Dashboard, Filtro Favorito, Relatório Salvo, Exportação, Agendamento de Atualização |

## D090/D149 — princípio central, mecanizado nesta lote

`analytics`/`reporting` **nunca** escrevem em nenhum bounded context operacional — só leem. D421
torna isso um contrato `import-linter` módulo-inteiro-contra-módulo-inteiro (mesmo formato de D405,
Lote 8): todo módulo operacional é proibido de importar `modules.analytics`/`modules.reporting`, em
qualquer camada. A direção inversa (`analytics` lendo `freight`, por exemplo) é exatamente o que o
`AnalyticsCalculationEngine` faz de propósito — provado por teste real, não simulado (D420).

## Auditorias obrigatórias (pedidas explicitamente pelo usuário)

1. Cálculo de Métrica respeitando sua versão (`metrica_versao` fixa no Indicador, mesmo depois da
   Métrica ganhar uma versão nova).
2. `IndicadorConsolidado` sem fórmula própria — resposta nunca inclui `formula`, só `metric_id`/
   `metric_version`.
3. Snapshot Analítico imutável depois de `CONSOLIDADO` (D151) — nenhum `PATCH`/recálculo possível.
4. Correção posterior de uma Viagem não altera um Snapshot antigo já consolidado.
5. Dashboard armazena configuração, nunca valores (D152) — sem coluna numérica de indicador.
6. Autorização/isolamento por tenant.
7. Exportação com erro rastreável (`FALHOU` sempre com `mensagem_erro` preenchida).
8. Novo contrato `import-linter` (D421).

## Critério de Definição de Pronto (D352)

Migration real, Repository testado, Application testado, E2E via HTTP, tenant isolation + auditoria
— aplicado às 9 entidades.

## Decisões

D418–D422 — ver [`../../product/DECISIONS.md`](../../product/DECISIONS.md).

## Achados deste lote (Sprint 11, Lote 11)

- **As 8 auditorias pedidas foram verificadas por teste real**, não só por leitura de código —
  `tests/integration/test_bi_flow.py` (7 testes, todos verdes contra Postgres real). Auditoria 1
  (versão pinada) e 4 (correção pós-Snapshot) são provadas na MESMA classe de teste
  (`TestSnapshotImmutabilityAudit`/`TestMetricVersioningAudit`), porque as duas dependem do mesmo
  fato físico: `ConsolidatedIndicator.valor`/`metrica_versao` são cópias fixas no momento do
  cálculo, nunca uma referência viva.
- **Auditoria 8 (D421) seguiu o mesmo precedente do Lote 1** (`DEPENDENCY_RULES.md`): prova pontual,
  não um teste pytest permanente. Injetamos manualmente `from modules.analytics.domain.entities.
  metric import Metric` em `freight/domain/entities/trip.py`, rodamos `lint-imports` — contrato
  "operational modules never import analytics/reporting" reportou `BROKEN` imediatamente (`10 kept,
  1 broken`) — revertemos a injeção e confirmamos `11 kept, 0 broken` de novo. O gate funciona.
- **`AnalyticsCalculationEngine` é a prova mecânica de D090/D149 rodando de verdade**: o teste cria
  uma Viagem real via `POST /viagens`, seta `receita_realizada` via `TripInternalTransitions`
  (D420, mesmo padrão "nunca alcançável por HTTP" de todo `*InternalTransitions` desde o Lote 5), e
  o motor lê essa Viagem via `SqlAlchemyTripRepository` — cross-module de verdade, sem mock.
- **Bug pego pelo próprio ciclo de implementação**: os 3 novos routers `DELETE` (`dashboard_router`/
  `saved_filter_router`/`saved_report_router`) inicialmente omitiam `response_model=None` no
  decorator — todo `DELETE` com `status_code=204` do projeto inteiro (24 endpoints anteriores,
  desde o Lote 2) sempre passa esse parâmetro explicitamente; sem ele, o FastAPI infere
  `response_model` a partir da anotação de retorno `-> None` e a própria inicialização do `app`
  falha (`AssertionError: Status code 204 must not have a response body`) — pego imediatamente ao
  rodar o primeiro teste de integração, antes de qualquer commit.
- **Isolamento de tenant + Platform Reference Data (D046) confirmado com os dois lados**: Métrica
  privada do Tenant A nunca aparece para o Tenant B (`404`); uma Métrica com `tenant_id IS NULL`
  inserida diretamente (não existe rota HTTP para criar Reference Data — `CreateMetricHandler`
  sempre grava `actor.tenant_id`) é visível para os dois tenants simultaneamente.
- **MinIO real reutilizado sem fricção** no teste de ciclo feliz de Exportação
  (`complete_export`/upload real via `PUT` na URL assinada) — mesma infraestrutura validada pela
  primeira vez no Lote 10, sem nenhuma surpresa nova aqui.
- **Suite completa**: 127 testes de integração verdes (127 passed, 2 deselected apenas
  Redis/RabbitMQ — pendência de infraestrutura pré-existente desde o Lote 1, não afetada por este
  lote). Nenhuma regressão cross-lote — diferente do Lote 10 (onde `DispatchTripHandler` disparava
  Notificação incidentalmente), `analytics`/`reporting` são módulos-folha (D421 garante que nada os
  importa de volta), então nenhum teste de outro lote toca nas tabelas novas.

## Como esta pasta cresce

Depois deste lote, por instrução explícita do usuário: **Lote 12 — IA** (princípio equivalente —
"IA sugere; IA nunca decide"), depois **Backend Freeze** (auditoria OpenAPI↔rotas, RBAC↔endpoints,
Alembic do zero, Redis+RabbitMQ reais), só então Frontend.
