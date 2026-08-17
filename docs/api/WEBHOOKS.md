# WEBHOOKS.md — Contrato de Webhooks

Direção invertida de toda a documentação anterior: aqui o **GestorFrete é o cliente HTTP**, chamando
um endpoint que o tenant configurou. A tabela física (`webhooks`, `relational/010-administracao.md`)
já existe — este documento é o contrato de comportamento sobre ela, não uma nova estrutura de dados.

## Fluxo

```
Evento de domínio ocorre (ex.: ViagemConcluida, EVENT_MAP.md)
        │
        ▼
Backend verifica: algum webhook do tenant tem esse evento em `eventos_assinados`?
        │  (índice GIN, INDEXES.md categoria 7, D198 — exatamente para esta consulta)
        ▼
Monta o payload, assina com HMAC (segredo de `segredo_hmac_arquivo_id`, D107)
        │
        ▼
POST para `url_destino`
        │
   ┌────┴────┐
  200 OK     Erro (timeout, 4xx, 5xx)
   │              │
   ▼              ▼
Entregue      Retry (ver política abaixo)
```

## Evento

Só eventos já catalogados em [`../product/EVENT_MAP.md`](../product/EVENT_MAP.md) podem ser
assinados — nunca um evento interno técnico (D105: evento técnico nunca é exposto diretamente, só o
evento de negócio interpretado). Exemplos reais already catalogados: `ViagemCriada`,
`ViagemDespachada`, `ViagemConcluida`, `ViagemEncerrada`, `EntregaRealizada`, `CanhotoRegistrado`.

`webhooks.eventos_assinados` (`JSONB`) guarda a lista de nomes de evento que aquele webhook recebe —
um tenant pode assinar um subconjunto, nunca "todos os eventos" implicitamente (assinatura explícita
por nome, sempre).

## Payload

```json
{
  "event": "ViagemConcluida",
  "occurred_at": "2026-07-30T14:32:00Z",
  "correlation_id": "e5f6g7h8-...",
  "tenant_id": "...",
  "data": {
    "viagem_id": "...",
    "codigo": "VG-2026-000123"
  }
}
```

`correlation_id` é o mesmo `id_correlacao` gravado em `logs_auditoria` para a transação que
originou o evento (D147) — permite ao tenant correlacionar o webhook recebido com qualquer suporte
futuro sobre aquela transação específica.

## Assinatura (segurança)

```
X-GestorFrete-Signature: sha256=<HMAC-SHA256(body, segredo)>
```

O tenant valida a assinatura usando o segredo mostrado uma única vez na tela de configuração do
webhook (armazenado como `segredo_hmac_arquivo_id`, D107 — nunca em texto claro no banco, mesmo
princípio de `senha_hash`/`token_hash`). Corpo (`body`) é assinado **antes** de qualquer
formatação/indentação adicional — o receptor deve calcular o HMAC sobre os bytes exatos recebidos.

## Retry e timeout

```
Tentativa 1 → falha (timeout ou 5xx)
        │
        ▼
Retry (backoff exponencial — intervalo exato não fixado aqui, calibrado com operação real)
        │
        ▼
Retry (repete até um número máximo de tentativas)
        │
        ▼
Máximo de tentativas esgotado → webhooks.status muda para SUSPENSO
```

- **Timeout** por chamada: um valor curto o suficiente para não travar a fila de entrega de outros
  eventos/tenants (valor exato de calibração de infraestrutura, não fixado aqui).
- **`4xx` do receptor não gera retry indefinido** — um `404`/`410` (endpoint não existe mais)
  suspende o webhook mais rápido que um `5xx` transitório, porque indica erro de configuração, não
  instabilidade momentânea.
- `webhooks_status_enum` já modela exatamente essa progressão: `ATIVO` → (falhas acumuladas) →
  `SUSPENSO`. Reativação (`SUSPENSO` → `ATIVO`) é uma ação explícita do tenant (corrigir a URL,
  reativar manualmente), nunca automática.

## Idempotência (do lado do receptor)

Cada entrega inclui um identificador de evento estável — o par `(tenant_id, event, correlation_id)`
ou um `event_id` próprio (a definir na implementação) — para que o receptor possa deduplicar se
receber o mesmo evento mais de uma vez (retry que teve sucesso, mas a confirmação `200 OK` se
perdeu na volta). Consistente com D111 ("Webhook → `event_id`" já citado como exemplo de atributo de
idempotência) — esta é a implementação HTTP daquela decisão.

## Replay

Reenvio manual de um evento já entregue (ex.: o tenant perdeu o webhook original por uma falha do
lado dele) é uma ação futura de suporte/administração — não um endpoint público desta sprint.
Quando implementado, reusa o mesmo payload/assinatura originais (nunca gera um evento "novo" com
timestamp atual para um fato que já aconteceu no passado).

## Estado, tentativa e resposta — o que é registrado

| O quê | Onde |
|---|---|
| Status do webhook (`ATIVO`/`INATIVO`/`SUSPENSO`) | `webhooks.status`, já físico |
| Histórico de tentativas de entrega (sucesso/falha, código HTTP recebido, tentativa N) | Não modelado ainda no Modelo Relacional — candidato a uma tabela `entregas_webhook`/`webhook_deliveries` própria (Histórica, mesmo padrão de `*_status_history`) se a necessidade de auditoria de entrega se confirmar; **não decidido nesta sprint**, registrado aqui como lacuna conhecida, não inventado agora |

## Segurança adicional

- `url_destino` só aceita `HTTPS` — nunca um endpoint de webhook em `HTTP` puro.
- Nenhum dado sensível (senha, token de outro sistema) é incluído no payload — só o necessário
  para o tenant buscar mais detalhe via API autenticada, se precisar.

## Como este documento cresce

A lacuna de "histórico de tentativas de entrega" (seção acima) é o item mais provável de virar uma
decisão registrada em `DECISIONS.md` + uma tabela nova no Modelo Relacional, quando o Backend
começar a implementar isso de fato — seguindo D101/D103 (Domain/Dictionary primeiro, nunca direto
na API).
