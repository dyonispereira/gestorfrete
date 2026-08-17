# CIOT_IMPLEMENTATION.md — CIOT

Aggregate Root de `documents`. Fonte: `flows/009-FISCAL.md`, `relational/007-fiscal.md`,
`041-ciot.md`. Aplicável só quando `Motorista.employment_type = AUTONOMO`.

## Máquina de estados

`PENDENTE` (`POST /ciots`) `→ REGISTRADO` (`commands/register`, chamada síncrona real — atribui
`codigo_ciot`/`protocolo_antt` na mesma resposta HTTP, sem passo assíncrono separado como CT-e/
MDF-e, D397). `PENDENTE`/`REGISTRADO → CANCELADO` (`commands/cancel`), só antes de
`Trip.status_operacional` avançar para `EM_DESLOCAMENTO` ou posterior.

## `POST /ciots`

`driver_id` deve referenciar Motorista com `employment_type = AUTONOMO` —
`FISCAL_CIOT_DRIVER_NOT_AUTONOMOUS` (422) caso contrário (leitura cross-module de
`DriverRepository`, `drivers`).

## `commands/register`

Simula a submissão à ANTT dentro do próprio Handler (sem `FiscalInternalTransitions` — D397): gera
`codigo_ciot`/`protocolo_antt` sintéticos e aplica a transição na mesma chamada, gravando também um
`EventoFiscal` (`documento_tipo=CIOT`, `tipo_evento=RESPOSTA`) para manter a mesma observabilidade
(D115) que CT-e/MDF-e têm via `FiscalInternalTransitions`. Idempotente pelo mesmo mecanismo:
`Idempotency-Key` HTTP (D211) mais `uq_ciots_protocolo_antt` como segunda camada de domínio.

## `commands/cancel`

`notes` obrigatória (D010). `FISCAL_CIOT_TRIP_ALREADY_STARTED` (409) quando
`Trip.status_operacional` já passou de `LIBERADA` — leitura cross-module de `TripRepository`.

## Sem XML/payload próprio

`ciots` não tem `xml_arquivo_id` (`041-ciot.md`, "Fora de escopo") — o payload técnico da chamada à
ANTT vive só em `eventos_fiscais.payload_arquivo_id`.

## Erros de domínio

`FISCAL_CIOT_NOT_FOUND` (404), `FISCAL_CIOT_DRIVER_NOT_AUTONOMOUS` (422), `FISCAL_CIOT_INVALID_
TRANSITION` (409), `FISCAL_CIOT_TRIP_ALREADY_STARTED` (409).

## Auditoria e tenant isolation

Toda transição grava `logs_auditoria` + uma linha em `ciots_status_history`.
`SqlAlchemyCiotRepository` filtra por `get_current_tenant_id()`.
