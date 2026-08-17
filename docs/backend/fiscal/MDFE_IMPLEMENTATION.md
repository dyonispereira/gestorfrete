# MDFE_IMPLEMENTATION.md — MDF-e

Aggregate Root de `documents`. Fonte: `flows/009-FISCAL.md`, `relational/007-fiscal.md`,
`040-mdfe.md`.

## Máquina de estados

`PENDENTE` (`POST /mdfes`, comando real — diferente de CT-e) `→ AUTORIZADO` (Externa, resposta
SEFAZ, `FiscalInternalTransitions.receive_mdfe_sefaz_response`, D397) `→ ENCERRADO`
(`commands/close`). `PENDENTE`/`AUTORIZADO → CANCELADO` (`commands/cancel`) — nunca a partir de
`ENCERRADO`.

## `POST /mdfes`

Todo `cte_id` em `cte_ids` deve pertencer à mesma `trip_id` e estar `AUTORIZADO` — validado por
leitura direta de `CteRepository` antes de criar o MDF-e; `FISCAL_MDFE_CTE_NOT_AUTHORIZED` (409)
caso contrário. `numero`/`serie` capturados de `configuracoes_fiscais_tenant` via `SELECT ... FOR
UPDATE` (D399), mesmo mecanismo do CT-e mas com seu próprio contador
(`proximo_numero_mdfe`/`serie_mdfe`). Cria as linhas de `mdfes_ctes` na mesma transação.

## `commands/close` (D398)

`AUTORIZADO→ENCERRADO`. Precondição real, verificada por leitura cross-module: todas as Entregas da
Viagem em status terminal (`DeliveryRepository.count_pending_for_trip(trip_id) == 0`) —
`FISCAL_MDFE_LAST_DELIVERY_PENDING` (409) caso contrário. `040-mdfe.md` descreve esta transição como
"normalmente derivada automaticamente" por um consumidor de `EntregaRealizada` — este lote não liga
esse gatilho automático a nenhum handler de `freight` (nenhum evento real dispara nada neste
backend, D375); `commands/close` é o único caminho reachável via HTTP, exatamente como a permissão
`documents.mdfe.close` já prevê para "confirmação manual" — não é um gap, é a única forma real de
chegar em `ENCERRADO` nesta fundação. Ao encerrar, chama
`TripInternalTransitions().record_fiscal_transition(trip_id, MDFE_ENCERRADO, now)`.

## `commands/cancel`

`notes` obrigatória (D010). `FISCAL_MDFE_INVALID_TRANSITION` (409) a partir de `ENCERRADO`.

## Erros de domínio

`FISCAL_MDFE_NOT_FOUND` (404), `FISCAL_MDFE_NO_CTE` (409, `cte_ids` vazio — também barrado por
`minItems: 1` no schema, redundante mas documentado), `FISCAL_MDFE_CTE_NOT_AUTHORIZED` (409),
`FISCAL_MDFE_INVALID_TRANSITION` (409), `FISCAL_MDFE_LAST_DELIVERY_PENDING` (409).

## Auditoria e tenant isolation

Toda transição grava `logs_auditoria` + uma linha em `mdfes_status_history`.
`SqlAlchemyMdfeRepository` filtra por `get_current_tenant_id()`.
