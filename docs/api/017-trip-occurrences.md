# 017 — Trip Occurrences

Bounded context proprietário: `freight` (D215). Ocorrência (D232 — sub-recurso de Viagem,
`ocorrencias.viagem_id NOT NULL`).

## Uma única entidade — nunca uma API por tipo

`ocorrencias.tipo` (`ocorrencias_tipo_enum`: `ATRASO`/`AVARIA`/`PANE`/`SINISTRO`/`OUTRO`) já cobre
todo o espectro (D076 — genérica por design, mesma nota já usada para Fornecedor em
`008-suppliers.md`). Nunca `POST /viagens/{id}/delays`, `/damages`, `/breakdowns` — um único
`POST /viagens/{id}/occurrences` com `type` no corpo.

```
GET/POST  /api/v1/viagens/{id}/occurrences
GET/PATCH /api/v1/viagens/{id}/occurrences/{occurrenceId}
```

**Sem `DELETE`** — mesma disciplina de Entrega (`015-trip-deliveries.md`): `RBAC_MATRIX.md` 7.13
só tem `freight.occurrence.view`/`.create`/`.edit`. Uma Ocorrência incorreta é corrigida via
`status: RESOLVIDA` + comentário, nunca removida (é registro de auditoria/segurança).

## `GET /api/v1/viagens/{id}/occurrences`

**Segurança**: `bearerAuth` + `freight.occurrence.view`.

**Query parameters**: `page`/`limit`, `type` (`tipo` — existe fisicamente, D226), `status`,
`severity` (`gravidade`).

**Responses**: `200` (`Pagination` de `Occurrence`, `trip-schemas.md`), `401`, `403`, `404`, `500`.

## `GET /api/v1/viagens/{id}/occurrences/{occurrenceId}`

**Segurança**: `freight.occurrence.view`. **Responses**: `200`, `401`, `403`, `404`, `500`.

## `POST /api/v1/viagens/{id}/occurrences`

**Segurança**: `freight.occurrence.create`. **`Idempotency-Key` obrigatória** quando `type` ∈
`{AVARIA, SINISTRO, PANE}` — seção 15 do pedido lista "registrar eventos críticos"; `ATRASO`/
`OUTRO` não exigem (evento informativo, sem efeito colateral crítico de domínio).

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          type: { type: string, enum: [ATRASO, AVARIA, PANE, SINISTRO, OUTRO] }
          description: { type: string }
          severity: { type: string, enum: [BAIXA, MEDIA, ALTA, CRITICA] }
          occurred_at: { type: string, format: date-time }
          location:
            type: object
            nullable: true
            properties:
              latitude: { type: number, format: double }
              longitude: { type: number, format: double }
        required: [type, description, occurred_at]
```

**Nota sobre `location`**: `ocorrencias` (Modelo Relacional, `relational/003-operacao.md`) **não
tem colunas de latitude/longitude próprias** — diferente de `viagem_status_history`, que tem. Se o
app capturar localização no momento do registro, ela é aceita aqui mas **atualmente não
persistida** em nenhuma coluna de `ocorrencias`; o dado real de localização da Viagem naquele
instante vive em `posicoes_veiculo` (rastreamento) ou, se a Ocorrência disparar uma transição de
status, no `latitude`/`longitude` da linha correspondente de `viagem_status_history`. Documentado
como lacuna conhecida (D226-adjacente — o campo existe no contrato porque faz sentido de produto,
mas não tem coluna física correspondente ainda), não removida do request nem inventada como se já
fosse persistida.

**Efeito colateral documentado**: toda Ocorrência dispara `OcorrenciaRegistrada`
(`EVENT_MAP.md`) — consumido por `notification_center`, `support`, `analytics`, `audit`. Tipo
`AVARIA` também dispara `AvariaRegistrada` (evento mais específico, mesma ação de API — um único
`POST` pode gerar dois eventos quando o tipo justificar, documentado explicitamente, nunca dois
endpoints).

**Responses**: `201` (`Occurrence`), `400`, `401`, `403`, `404`, `409` (Idempotency-Key), `500`.

## `PATCH /api/v1/viagens/{id}/occurrences/{occurrenceId}`

**Segurança**: `freight.occurrence.edit`. D229 — parcial. Uso principal: `status: RESOLVIDA`.

**Responses**: `200`, `400`, `401`, `403`, `404`, `500`.

## Relação com Interromper Viagem — nunca automática

Registrar uma Ocorrência `SINISTRO`/`PANE` **não** move a Viagem para `INTERROMPIDA`
automaticamente — são ações separadas e deliberadas (`018-trip-status.md`,
`commands/interromper`). O flow (`002-VIAGEM.md`) descreve os dois como relacionados na prática
("Sinistro... → Viagem vai para INTERROMPIDA"), mas o contrato não infere a transição de estado a
partir do tipo de Ocorrência — quem opera decide explicitamente se aquela Ocorrência específica
justifica interromper a Viagem, evitando uma Ocorrência de baixa gravidade (`ATRASO`, por exemplo)
disparar uma interrupção não intencional.

## Como este documento cresce

Nenhuma mudança prevista — se `location` ganhar coluna física em `ocorrencias` (decisão futura,
Domain primeiro, D101), este documento passa a marcar o campo como persistido de verdade.
