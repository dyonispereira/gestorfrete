# REPORTING_IMPLEMENTATION.md — Dashboard/Filtro/Relatório/Exportação/Agendamento (066-070)

Bounded context `reporting` (`apps/api/src/modules/reporting/`).

## Dashboard (066) — nunca guarda valor (D152)

CRUD + `commands/share` (altera só `permissoes_compartilhamento`, separado de `PATCH` porque
compartilhar é RBAC-sensível, D234-style). `GET` combina próprios (`.view_own`) + compartilhados
(`.view_shared`) conforme o que o ator tiver — cada permissão checada independentemente, nunca uma
exige a outra. `widgets`/`layout`/`filtros`/`preferencias` são sempre JSONB de configuração — nenhum
campo numérico de indicador existe na tabela (`dashboards_personalizados`), então D152 é reforçado
estruturalmente, não só por convenção de código.

## Filtro Favorito (067) — sempre pessoal

CRUD simples, sempre `usuario_id` da sessão (nunca aceito no corpo). Sem conceito de
compartilhamento (diferente de Dashboard) — pedido explícito do contrato.

## Relatório Salvo (068) — definição, nunca query física

CRUD simples; `metric_ids` validados contra `analytics` (404 se algum não existe) no momento da
criação — mas o Relatório em si só guarda a referência, nunca resolve/executa nada até uma
Exportação ser solicitada.

## Exportação (069) — assíncrona, contexto sempre completo (D157)

`CreateExportHandler`: se `saved_report_id` informado, resolve `metric_ids`/`filters` REAIS do
Relatório Salvo **no momento da chamada** (nunca aceita esses campos como cópia literal do corpo,
mesmo se o cliente os enviar) — captura `filtros_utilizados`/`periodo`/`metricas_versoes` (D160-
style, `{metric_id, version}` de cada Métrica envolvida, sempre a versão atual no momento da
solicitação). Cria `PROCESSANDO`, nunca `CONCLUIDA` na mesma transação (D307). `ReportingInternalTransitions`
(mesmo espírito de `*InternalTransitions`) expõe `complete_export(export_id, file_id, now)` e
`fail_export(export_id, error_message, now)` — simulam o processamento assíncrono que este lote não
constrói de verdade (nenhum motor de geração de PDF/Excel/CSV real, fora de escopo). `Idempotency-
Key` mesmo tratamento de D418 (declarado, não reforçado).
`ReportingInternalTransitions.complete_export(export_id, file_id)`/`fail_export(export_id,
error_message)` — sem `now`: `exportacoes_geradas` só tem `data_hora_solicitacao` na DDL congelada,
nenhuma coluna de conclusão/falha (mesma família de achado do D422 em Dashboard).

## Agendamento de Atualização (070) — nunca calcula (D159)

CRUD simples; `ck_agendamentos_atualizacao_alvo` (exatamente um de `metric_id`/`cube_id`) reforçado
na Application (`400` se nenhum ou os dois). Alvo não é editável via `PATCH` — trocar o alvo é criar
um novo Agendamento.

## Auditorias deste lote (candidatas)

1. **Dashboard nunca persiste valor** — inspeção da tabela/schema confirma ausência de coluna
   numérica de indicador; um widget referencia `metric_id`/`indicator_id`, nunca um valor.
2. **`view_shared` nunca concede edição** — usuário com Dashboard compartilhado consegue `GET` mas
   `PATCH`/`DELETE` continuam `403` sem `.edit_own`/`.delete_own` (que só o dono tem).
3. **Export com erro rastreável** — `fail_export` sempre exige `error_message` não vazio; resposta
   `FALHOU` sem `arquivo_id`.
4. **Contexto de Export sempre capturado no momento da chamada** — editar um Relatório Salvo depois
   de uma Exportação já concluída não altera `filtros_utilizados`/`metricas_versoes` daquela
   Exportação passada (histórica, D157).
5. **Isolamento por tenant/usuário** — Filtro Favorito/Relatório Salvo de um usuário nunca visível a
   outro sem a permissão de dono correspondente.

## Achados deste lote

- Todas as 5 auditorias candidatas foram confirmadas por teste real
  (`tests/integration/test_bi_flow.py`), incluindo o ciclo completo de compartilhamento de
  Dashboard: dono cria `PRIVADO` → segundo usuário com `view_shared` recebe `403` → dono compartilha
  (`commands/share`) → mesmo usuário agora recebe `200` e o Dashboard aparece na listagem → um
  terceiro usuário com `view_own` mas SEM `view_shared` continua `403` mesmo depois do
  compartilhamento — prova que as duas permissões são checadas de forma independente, nunca uma
  implica a outra.
- **`Dashboard` chegou a nascer com um campo `audit: AuditMetadata` real** (com `update()`/`share()`
  chamando `self.audit.touched(...)`), até uma checagem literal da DDL congelada (`grep` em
  `relational/011-bi.md` por `criado_em`/`atualizado_em`/`excluido_em`/`criado_por` — zero matches
  nas 9 tabelas de BI) mostrar que nenhuma das 5 tabelas de `reporting` tem coluna de auditoria.
  Reescrito para D422: `archive()` (`status=ARQUIVADO`) como mecanismo físico de soft delete,
  `DashboardResponse` omite `audit` inteiramente — mesmo precedente de `IntegrationConfigResponse`/
  `WebhookResponse` (Lote 10).
- **Bug pego pelo primeiro teste de integração, antes de qualquer commit**: os 3 novos `DELETE`
  (`dashboard_router`/`saved_filter_router`/`saved_report_router`) inicialmente esqueceram
  `response_model=None` no decorator do FastAPI — todo outro `DELETE` com `status_code=204` do
  projeto (24 endpoints anteriores) sempre passa esse parâmetro; sem ele, a própria inicialização do
  `app` falha (`AssertionError: Status code 204 must not have a response body`), porque o FastAPI
  infere `response_model` a partir da anotação `-> None`.
- D157 (contexto de Export sempre capturado no momento da chamada, nunca aceito do cliente) foi
  testado adversarialmente: o teste envia `saved_report_id` E um `filters` "adulterado" no mesmo
  corpo da requisição — a resposta confirma que `filters_used` reflete os filtros REAIS do Relatório
  Salvo, nunca o valor adulterado enviado pelo cliente.
