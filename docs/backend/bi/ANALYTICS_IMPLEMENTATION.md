# ANALYTICS_IMPLEMENTATION.md — Métrica/Indicador/Snapshot/Cubo (062-065)

Bounded context `analytics` (`apps/api/src/modules/analytics/`).

## Métrica (062) — versionamento sem coluna de encadeamento (D419)

`Metric.new_version(previous)` cria uma linha **totalmente nova** (`id` novo, `versao =
previous.versao + 1`, mesmo `nome`) — nunca um `UPDATE` em `formula`. `MetricRepository.
get_latest_by_name(nome, tenant_id)` resolve "a versão atual" via `ORDER BY versao DESC LIMIT 1`.
`CreateMetricHandler` checa unicidade de `nome` consultando a versão mais recente de qualquer
lingagem existente (nunca uma constraint física — `metricas` não tem `UNIQUE(tenant_id, nome)` de
propósito, D419) antes de permitir `versao=1` nova. `UpdateMetricHandler`: se `formula` mudou,
delega para `new_version`; demais campos (`name`/`unit`/`data_sources`/`calculation_periodicity`/
`status`) editam a MESMA linha (nunca geram versão nova).

## Indicador Consolidado (063) — só leitura via HTTP, escrita só via `AnalyticsCalculationEngine`

Sem `POST`/`PATCH`/`DELETE` no router — `062`/`063` são explícitos: "todo Indicador Consolidado
nasce do processamento interno". `AnalyticsCalculationEngine` (D420, mesmo espírito de
`TripInternalTransitions`) expõe `calculate_trip_revenue_indicator(metric_id, trip_id, now)`: lê
`viagens.receita_realizada` de verdade (via `SqlAlchemyTripRepository`, cross-module — a prova
mecânica de D090/D149), grava um `IndicadorConsolidado` com `dimensao_tipo=VIAGEM`,
`dimensao_id=trip.id`, `metrica_versao` fixa (cópia do `metrica.versao` no momento do cálculo).
Recalcular a mesma Métrica/dimensão/período marca o indicador anterior `RECALCULADO` (nunca
apagado) antes de inserir o novo `VALIDO` — nunca dois `VALIDO` para a mesma tripla.

## Snapshot Analítico (064) — `POST` só inicia, imutável depois de `CONSOLIDADO`

`CreateSnapshotHandler` cria `EM_PROCESSAMENTO`, `origem_processamento=MANUAL` sempre (`AUTOMATICO`
reservado a `Agendamento de Atualização`, D159, nunca aceito no corpo). `409
ANALYTICS_SNAPSHOT_PERIOD_ALREADY_CONSOLIDATED` se já existe um Snapshot `CONSOLIDADO` para o mesmo
`periodo_referencia`+tenant. `AnalyticsCalculationEngine.consolidate_snapshot(snapshot_id,
indicator_ids, now)` — simula o processamento assíncrono (D151 reforçado ao máximo): vincula os
Indicadores via `snapshots_analiticos_indicadores`, marca cada um `SNAPSHOTADO` (nunca mais
recalculável — `AnalyticsCalculationEngine` recusa recalcular um indicador já `SNAPSHOTADO`), grava
o Snapshot passa a `CONSOLIDADO`. D160 — "quais Métricas participaram" NUNCA é uma coluna própria
(a DDL congelada não tem `metricas_participantes`): `participating_metrics` na resposta HTTP é
sempre derivado em tempo de leitura via JOIN `snapshots_analiticos_indicadores` →
`indicadores_consolidados` (`AnalyticalSnapshotRepository.get_participating_metrics`). Nenhum
`PATCH`/`DELETE` existe no router — corrigir depois de
`CONSOLIDADO` exige um novo Snapshot, nunca reabrir o antigo (D151 absoluto).

## Cubo Analítico (065) — só metadado estrutural

CRUD simples (`dimensoes`/`metricas_ids`), nenhuma tabela de dado materializado — a própria
definição já é o produto final desta fundação (`cubos_analiticos_metricas` só a relação N:N).

## `Idempotency-Key` — declarado, não reforçado (D418)

`POST /analytics/snapshots` aceita o cabeçalho (schema Pydantic o resolve, mas nada é feito com o
valor) — mesmo tratamento (não construído) de todo endpoint "obrigatório" anterior desde o Lote 2;
gap pré-existente do projeto inteiro, agora explicitamente registrado, não corrigido silenciosamente
aqui (infraestrutura cross-cutting que pertence a `core`, fora do escopo deste lote).

## Auditorias deste lote (candidatas)

1. **Versão pinada** — Métrica ganha uma nova versão (`formula` mudou), um Indicador já calculado
   com a versão antiga continua reportando `metric_version` antigo, nunca o novo.
2. **Indicador nunca tem fórmula** — resposta HTTP nunca inclui `formula`.
3. **Snapshot imutável** — depois de `CONSOLIDADO`, tentar recalcular um Indicador já `SNAPSHOTADO`
   via `AnalyticsCalculationEngine` é recusado (`ConflictError`).
4. **Correção posterior não afeta Snapshot antigo** — Trip.receita_realizada corrigida depois do
   fechamento não muda o `valor` já gravado no Indicador `SNAPSHOTADO`.
5. **Isolamento por tenant** — Métrica de um tenant nunca aparece na listagem de outro (exceto
   Platform Reference Data, `tenant_id IS NULL`, visível a todos).

## Achados deste lote

- As 5 auditorias candidatas acima foram todas confirmadas por teste real contra Postgres
  (`tests/integration/test_bi_flow.py`), não só por leitura de código.
- Durante a implementação, a entidade/modelo de `AnalyticalSnapshot` chegou a nascer com um campo
  `metricas_participantes` (JSONB) que não existe na DDL congelada (`relational/011-bi.md` é
  explícito: D160 é sempre derivado via junção, nunca uma coluna própria). Pego ao reconferir a DDL
  literalmente antes de gerar a migration — removido da entidade e do modelo antes de qualquer
  `alembic revision`, então nunca chegou a existir fisicamente no banco.
- `ConsolidatedIndicatorRepository` originalmente só tinha `get_current_valid` (filtrando
  `status=VALIDO`), insuficiente para o guard de imutabilidade: se o único registro existente para
  uma tripla Métrica/dimensão/período já estivesse `SNAPSHOTADO`, o método devolvia `None` e o motor
  criaria um segundo indicador "ativo" silenciosamente, violando D151. Renomeado para `get_latest`
  (mais recente, qualquer status) e `AnalyticsCalculationEngine` passou a checar os dois status
  (`SNAPSHOTADO` → recusa; `VALIDO` → marca `RECALCULADO` e cria o novo) como ramos explícitos.
- `AnalyticsCalculationEngine.calculate_trip_revenue_indicator` é hoje o único calculador real
  (receita de Viagem); `Cubo Analítico`/demais dimensões (`VEICULO`/`MOTORISTA`/`CLIENTE`/`TENANT`)
  ficam com a granularidade dimensional já modelada na Métrica, mas sem um segundo calculador
  concreto nesta fundação — não pedido pelo usuário para este lote, registrado aqui para quando o
  próximo calculador for necessário.
