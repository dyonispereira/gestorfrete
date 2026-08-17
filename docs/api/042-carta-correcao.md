# 042 — Carta de Correção (CC-e)

Bounded context proprietário: `documents` (D215). **D282/D009-FISCAL.md**: "Não é uma transição de
status — é um registro adicional anexado a um CT-e já `AUTORIZADO`". Nunca altera o CT-e
diretamente (o CT-e permanece `AUTORIZADO`, `039-cte.md` não ganha um comando de "corrigir") —
sub-recurso com ciclo de vida próprio (D225).

## `GET /api/v1/ctes/{id}/cartas-correcao`

**Segurança**: `bearerAuth` + `documents.cte.correct` — `RBAC_MATRIX.md` §7.17 não distingue
"visualizar carta de correção" de "emitir carta de correção"; `.correct` cobre os dois (mesma
família de reaproveitamento coarse-grained já documentada em `039`).

**Responses**: `200` (`Pagination` de `CorrectionLetter`, `fiscal-schemas.md`), `401`, `403`, `404`,
`500`.

## `GET /api/v1/ctes/{id}/cartas-correcao/{cartaId}`

**Responses**: `200`, `401`, `403`, `404`, `500`.

## `POST /api/v1/ctes/{id}/cartas-correcao`

Só aceito quando o CT-e pai está `AUTORIZADO` (`ck` de aplicação, `009-FISCAL.md`) — correção de
erros formais que **não alteram valores fiscais nem partes envolvidas** (ex: erro de digitação em
observações); mudanças de valor/partes exigem cancelamento + reemissão (`039-cte.md`), nunca uma
Carta de Correção.

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          correction_text: { type: string }
        required: [correction_text]
```

`sequence_number` nunca vem do corpo — calculado pela aplicação (`uq_cartas_correcao_cte_id_
sequencial`, sempre o próximo da série para este CT-e).

**Segurança**: `documents.cte.correct`. **Idempotency-Key**: recomendado (evita duplicar carta por
retry de rede).

**Responses**: `201` (`CorrectionLetter`), `400`, `401`, `403`, `404` (CT-e não existe), `409` —
`FISCAL_CTE_NOT_AUTHORIZED` (CT-e pai não está `AUTORIZADO`), `500`.

## Sem `PATCH`/`DELETE`

Carta de Correção é, ela mesma, um registro de correção — corrigir uma CC-e errada é emitir uma
nova CC-e (próximo `sequence_number`), nunca editar/excluir a existente (D109 — nenhum documento
fiscal é excluído fisicamente, mesmo um artefato de correção).

## `GET /api/v1/ctes/{id}/cartas-correcao/{cartaId}/xml`

Mesmo padrão de `039`/`040` — referência a Storage (D276), nunca o binário.

**Responses**: `200` (`{ xml_file_id, generated_at }`), `401`, `403`, `404`, `500`.

## Como este documento cresce

Nenhuma mudança estrutural prevista — CC-e é, por definição regulatória, um artefato append-only
simples (sequência + texto + XML), estável desde a fundação deste lote.
