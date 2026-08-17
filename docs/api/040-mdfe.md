# 040 — MDF-e (Manifesto Eletrônico de Documentos Fiscais)

Bounded context proprietário: `documents` (D215). Mesma filosofia de `039-cte.md`: aggregate
próprio, status próprio, histórico próprio, protocolo SEFAZ, XML em Storage — máquina mais simples
que a de CT-e (4 estados, sem os passos intermediários VALIDADO/ASSINADO/TRANSMITIDO — respeitado
literalmente, nenhum estado extra inventado por simetria com CT-e).

## `GET /api/v1/mdfes`

**Segurança**: `bearerAuth` + `documents.mdfe.view`.

**Query parameters**: `page`/`limit`, `trip_id` (`viagem_id`), `status`, `series` (`serie`).

**Responses**: `200` (`Pagination` de `MDFe`, `fiscal-schemas.md`), `401`, `403`, `500`.

## `GET /api/v1/mdfes/{id}`

**Responses**: `200` (`MDFe`), `401`, `403`, `404`, `500`.

## `POST /api/v1/mdfes`

Diferente do CT-e, MDF-e **é** criado via um comando explícito — a decisão de "quais CT-e consolidar
neste MDF-e" é do Faturista, não puramente automática (`009-FISCAL.md`: "MDF-e emitido, consolidando
um ou mais CT-e"). `status` nasce `PENDENTE`; a transição para `AUTORIZADO` acontece de forma
assíncrona (resposta SEFAZ), mesmo padrão de `039`.

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          trip_id: { $ref: "components/schemas.md#/UUID" }
          cte_ids:
            type: array
            items: { $ref: "components/schemas.md#/UUID" }
            minItems: 1
        required: [trip_id, cte_ids]
```

Todo `cte_id` deve referenciar um CT-e `status = AUTORIZADO` da mesma Viagem — `409` caso contrário
(`FISCAL_MDFE_CTE_NOT_AUTHORIZED`).

**Segurança**: `documents.mdfe.issue`. **Idempotency-Key**: obrigatório (D211).

**Responses**: `201` (`MDFe`), `400`, `401`, `403`, `404` (Viagem/CT-e não existe), `409` —
`FISCAL_MDFE_CTE_NOT_AUTHORIZED` / `FISCAL_MDFE_NO_CTE`, `500`.

## `PENDENTE → AUTORIZADO` — Externa

Resposta da SEFAZ, entregue via consumidor interno de Evento Fiscal (mesmo padrão de `039`) — nenhum
endpoint dispara diretamente.

## `commands/close`

`AUTORIZADO → ENCERRADO`. Precondição de domínio: última Entrega da Viagem concluída
(`EntregaRealizada`, `009-FISCAL.md`) — normalmente derivada automaticamente pelo consumidor desse
evento, mas `documents.mdfe.close` existe como permissão explícita para confirmação manual em casos
excepcionais (ex: consumidor automático falhou, Faturista confirma depois de verificar
manualmente). **Consequência direta em D019**: enquanto este MDF-e não atingir `ENCERRADO`, a Viagem
correspondente nunca atinge `ENCERRADA`, mesmo com a operação fisicamente concluída.

**Segurança**: `documents.mdfe.close`. **Idempotency-Key**: obrigatório.

**Responses**: `200` (`MDFe`, D238), `401`, `403`, `404`, `409` —
`FISCAL_MDFE_LAST_DELIVERY_PENDING` / `FISCAL_MDFE_INVALID_TRANSITION`, `500`.

## `commands/cancel`

`PENDENTE`/`AUTORIZADO → CANCELADO`. **Nunca permitido a partir de `ENCERRADO`**
(`009-FISCAL.md`, transição inválida normativa).

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          notes: { type: string }
        required: [notes]
```

**Segurança**: `documents.mdfe.cancel` (Aprovação: Diretor). **Idempotency-Key**: obrigatório.

**Responses**: `200`, `400`, `401`, `403`, `404`, `409` — `FISCAL_MDFE_INVALID_TRANSITION`, `500`.

## `GET /api/v1/mdfes/{id}/status-history`

Mesmo padrão de `039` — leitura pura, cursor-paginada, D281.

**Segurança**: `documents.mdfe.view`.

**Responses**: `200` (coleção cursor-paginada de `MDFeStatusHistoryEntry`), `401`, `403`, `404`,
`500`. **Sem `POST`/`PATCH`/`DELETE`**.

## `GET /api/v1/mdfes/{id}/xml`

Mesmo padrão de `039` — referência, nunca o binário (D276).

**Responses**: `200` (`{ xml_file_id, generated_at }`), `401`, `403`, `404`, `500`.

## Como este documento cresce

Nenhuma mudança estrutural prevista — a máquina de 4 estados é estável; se a contingência SEFAZ
exigir um estado intermediário no futuro, isso é decisão de Domain primeiro (D101), nunca inventado
aqui por analogia com o CT-e.
