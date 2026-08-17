# FISCAL_EVENTS_IMPLEMENTATION.md — Evento Fiscal

`eventos_fiscais` — log técnico bruto (D105), distinto dos `*_status_history` de negócio (D281).
Fonte: `relational/007-fiscal.md`, `044-eventos-fiscais.md`.

## Somente leitura para usuários (D277)

Nenhum comando cria um `FiscalEvent` diretamente — toda linha nasce como efeito colateral de
`commands/transmit` (CT-e, requisição) + `FiscalInternalTransitions.receive_cte_sefaz_response`
(resposta), o par equivalente de MDF-e, e `commands/register` do CIOT (requisição+resposta na
mesma chamada, D397).

## Particionamento (reaplicação de D346/D364)

`PARTITION BY RANGE (data_hora_inicio)`, criada via SQL bruto na migration, com uma partição
`DEFAULT`. `duracao_ms` é `GENERATED ALWAYS AS (...) STORED` — mapeado com `sqlalchemy.Computed(...)`
desde o primeiro rascunho do model (reaplicação proativa de D382).

## Idempotência (Auditoria #1/#5 do usuário)

`uq_eventos_fiscais_documento_protocolo` (`documento_tipo`, `documento_id`, `protocolo_externo`)
garante que a mesma combinação nunca duplica — `FiscalInternalTransitions` sempre verifica essa
unicidade antes de inserir (mesmo padrão de `uq_ctes_protocolo_sefaz`), então mesmo sob condição de
corrida a constraint física é a última linha de defesa.

## `GET /fiscal/events`

Cursor-paginado (Categoria Física Time Series). Filtros: `document_type`/`document_id`/
`external_protocol`/`started_at__gte`/`__lte`/`result`/`origin`/`attempt_number` — todos sobre
coluna física real (D226).

## Erros de domínio

`FISCAL_EVENT_NOT_FOUND` (404).

## Auditoria e tenant isolation

`SqlAlchemyFiscalEventRepository` filtra por `get_current_tenant_id()`. Não grava `logs_auditoria`
próprio — é ele mesmo o log técnico (mesmo raciocínio de `logs_auditoria` não auditar a si mesmo).
