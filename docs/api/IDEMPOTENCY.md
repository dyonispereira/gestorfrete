# IDEMPOTENCY.md — Idempotência na Camada HTTP

## D211 — Idempotência para comandos críticos

Operações sensíveis devem suportar `Idempotency-Key`. Este documento é a camada HTTP das decisões
já tomadas na modelagem de domínio/dados — **D111** ("toda integração externa declara
explicitamente qual atributo garante idempotência") e **D138** ("todo comando da Fila de
Sincronização deve ser reexecutável sem efeito colateral") — nunca uma decisão nova e
desconectada delas.

## Quando é obrigatório

| Categoria de operação | Exemplos | `Idempotency-Key` |
|---|---|---|
| Emissão fiscal | `POST /api/v1/ctes` (emitir), `POST /api/v1/mdfes` | **Obrigatório** |
| Criação de recurso com efeito financeiro | `POST /api/v1/viagens`, `POST /api/v1/faturas` | **Obrigatório** |
| Sincronização mobile | `POST /api/v1/sync/*` (fila de sincronização, D138) | **Obrigatório** — a própria `filas_sincronizacao.identificador_local_unico` já é o equivalente de domínio; a API expõe isso como `Idempotency-Key` na borda HTTP |
| Pagamentos/cobranças | Qualquer endpoint que dispare cobrança real (`subscription`/`billing`) | **Obrigatório** |
| Webhooks (entrada, se algum dia a plataforma receber webhook de terceiro) | — | **Obrigatório**, mesma lógica |
| Comandos de domínio nomeados (D203-style, `POST /viagens/{id}/despachar`) | Ações que mudam estado uma única vez | **Obrigatório** |
| `GET` | Qualquer leitura | Não aplicável — `GET` já é idempotente por natureza (`NAMING_CONVENTION.md` seção 5) |
| `PATCH` de atualização simples (ex.: renomear um Centro de Custo) | — | Opcional — `PATCH` já é naturalmente idempotente (mesmo corpo, mesmo resultado); `Idempotency-Key` só ajuda contra duplo-clique/retry de rede, não é uma garantia de domínio ali |

## Formato

```
Idempotency-Key: 5f461a3c-c532-4bf3-b868-e1f0c5e7d538
```

- Sempre um `UUID` gerado pelo **cliente** (Frontend/App/integração), nunca pelo servidor — o
  propósito é o cliente conseguir reenviar a mesma chave num retry.
- Escopo da chave: `(tenant_id, Idempotency-Key)` — a mesma chave usada por tenants diferentes não
  colide (cada tenant tem seu próprio espaço de chaves).

## Retenção

A chave e a resposta original ficam retidas por **24 horas** (valor de partida — mesmo espírito de
`RATE_LIMITING.md`, ajustável com dado real de retry em produção, não uma lei imutável). Depois
disso, a mesma chave pode ser reutilizada como se fosse nova (o cenário de retry legítimo não
deveria levar mais que minutos; 24h cobre folga generosa sem reter estado indefinidamente).

## Comportamento

```
Requisição chega com Idempotency-Key
        │
        ▼
Chave já vista para este tenant, nas últimas 24h?
        │
   ┌────┴────┐
  Não        Sim
   │          │
   ▼          ▼
Processa   Payload da requisição é idêntico ao da primeira vez?
normalmente     │
   │       ┌────┴────┐
   │      Sim         Não
   │       │           │
   │       ▼           ▼
   │  Retorna a    409 Conflict
   │  resposta        (IDEMPOTENCY_KEY_PAYLOAD_MISMATCH,
   │  original,       ERROR_MODEL.md)
   │  sem reprocessar
   │  (mesmo status
   │  HTTP de então)
   ▼
Grava (chave, hash do payload, resposta) antes de retornar
```

- **Mesma chave + mesmo payload** → retorna a resposta original, sem efeito colateral duplicado
  (nunca emite um segundo CT-e, nunca cria uma segunda Viagem).
- **Mesma chave + payload diferente** → `409 Conflict` com `error.code =
  IDEMPOTENCY_KEY_PAYLOAD_MISMATCH` — nunca processa o novo payload silenciosamente sob a chave
  antiga (isso mascararia um bug do cliente, que reusou uma chave para uma operação diferente).
- Comparação de payload é por hash (ex.: SHA-256 do corpo normalizado), não por igualdade textual
  ingênua (evita falso-positivo por diferença de formatação de espaço/ordem de campo JSON).

## Retry em falha

Se a primeira tentativa falhou **antes** de gravar (ex.: erro `500` em processamento, requisição
nunca chegou a concluir), a chave não fica marcada como "usada" — um retry com a mesma chave
processa normalmente, não retorna o erro antigo como se fosse a resposta definitiva. Só uma
resposta de **sucesso** (ou uma falha de negócio definitiva, ex.: `422`) é retida como "resposta
original" para efeito de idempotência — um `500` transitório nunca é.

## Relação com idempotência já modelada no banco

Este documento não substitui nenhuma constraint física já catalogada em
[`../database/CONSTRAINTS.md`](../database/CONSTRAINTS.md) categoria 6 (Idempotência) —
`protocolo_sefaz`, `protocolo_antt`, `identificador_local_unico`, `token_hash` continuam sendo a
garantia de última instância no banco. `Idempotency-Key` na API é a primeira camada de defesa (evita
que a requisição duplicada sequer chegue a gerar um segundo protocolo) — as duas camadas trabalham
juntas, nenhuma substitui a outra (defesa em profundidade, mesmo princípio já usado em D193 para
`tenant_id`).

## Como este documento cresce

Estável. Todo novo endpoint de comando crítico (Lote 2 em diante) declara explicitamente se exige
`Idempotency-Key` no próprio contrato OpenAPI — nunca assumido implicitamente.
