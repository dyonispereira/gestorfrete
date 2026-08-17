# ERROR_MODEL.md — Modelo de Erros

## D209 — Erros possuem código estável

Mensagens podem mudar (tradução, redação); **`error.code` não deve ser reutilizado para
significados diferentes** — uma vez publicado, um código de erro é uma promessa de contrato, igual
a uma permissão (`permissoes.codigo`, D057) ou a um bounded context (D011): nunca renomeado com o
mesmo texto significando outra coisa, aposentado em vez de reciclado.

## Envelope único

```json
{
  "error": {
    "code": "FREIGHT_TRIP_NOT_FOUND",
    "message": "Viagem não encontrada.",
    "details": [],
    "request_id": "a1b2c3d4-...",
    "correlation_id": "e5f6g7h8-..."
  }
}
```

- `code`: estável, em `SCREAMING_SNAKE_CASE`, prefixado pelo bounded context em inglês (D011) —
  `FREIGHT_TRIP_NOT_FOUND`, `FINANCIAL_INVOICE_ALREADY_PAID`, `IDENTITY_INVALID_CREDENTIALS`.
- `message`: em português, para exibição direta ao usuário quando apropriado — pode mudar entre
  versões, nunca é usado para lógica no Frontend (o Frontend decide comportamento pelo `code`,
  nunca fazendo `if (message === "...")`).
- `details`: array, vazio quando não aplicável; populado em erro de validação (seção "Erro de
  validação" abaixo).
- `request_id`/`correlation_id`: sempre presentes, espelham os headers de
  `OPENAPI_ARCHITECTURE.md` seção 4 — permite ao suporte/observabilidade encontrar o log técnico
  exato (e, quando aplicável, a linha correspondente em `logs_auditoria`) a partir do erro que o
  usuário reportou.

**Nunca stack trace, nunca mensagem de exceção interna do Python/SQL bruta** no corpo da resposta,
em nenhum ambiente — nem Development. Detalhe técnico completo vai para o log do servidor
(correlacionado por `request_id`), nunca para o cliente HTTP.

## Categorias de erro

| Categoria | Código HTTP | Exemplo de `code` | Quando |
|---|---|---|---|
| Autenticação | `401` | `IDENTITY_INVALID_CREDENTIALS`, `IDENTITY_TOKEN_EXPIRED` | Token ausente, inválido ou expirado |
| Autorização (RBAC) | `403` | `IDENTITY_PERMISSION_DENIED` | Autenticado, mas sem a Permissão/Escopo necessário (D212) |
| Validação | `400` | `VALIDATION_FAILED` (genérico, `details` traz o detalhe por campo) | Payload sintaticamente inválido — tipo errado, campo obrigatório ausente |
| Regra de negócio | `422` | `FREIGHT_TRIP_INVALID_STATUS_TRANSITION`, `MAINTENANCE_ORDER_ALREADY_APPROVED` | Payload válido, mas viola um invariante de domínio |
| Conflito | `409` | `IDEMPOTENCY_KEY_PAYLOAD_MISMATCH` (`IDEMPOTENCY.md`), `UNIQUE_CONSTRAINT_VIOLATION` | Estado atual conflita com a operação pedida |
| Recurso inexistente | `404` | `FREIGHT_TRIP_NOT_FOUND` | Recurso não existe **ou existe em outro tenant** — nunca `403` nesse segundo caso (ver nota abaixo) |
| Integração externa | `502`/`504` | `FISCAL_SEFAZ_UNAVAILABLE`, `FISCAL_SEFAZ_TIMEOUT` | Falha ao comunicar com SEFAZ/ANTT/gateway de pagamento — nunca traduzido para `500` genérico, o cliente precisa saber que a causa é externa |
| Erro interno | `500` | `INTERNAL_SERVER_ERROR` | Qualquer falha não prevista — sempre logada com `request_id`, nunca detalhada ao cliente |

**Nota de segurança (recurso de outro tenant)**: pedir `/api/v1/viagens/{id}` de uma Viagem que
existe, mas pertence a outro tenant, retorna `404`, nunca `403` — `403` revelaria que o recurso
existe (ainda que em outro tenant), vazando informação. O mesmo princípio de "não vazar existência"
já se aplica a e-mail de login inválido (mensagem genérica, nunca "e-mail não encontrado" vs. "senha
incorreta" diferenciados).

## Erro de validação — formato de `details`

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Um ou mais campos são inválidos.",
    "details": [
      { "field": "data_programada", "code": "REQUIRED", "message": "Campo obrigatório." },
      { "field": "cliente_id", "code": "INVALID_UUID", "message": "Formato de UUID inválido." }
    ],
    "request_id": "..."
  }
}
```

Gerado automaticamente pela validação Pydantic do Backend — o Controller nunca escreve essa
tradução manualmente (D214, controller não conhece regra de domínio nem detalhe de validação além
de delegar ao schema).

## Como este documento cresce

Todo `error.code` novo é catalogado (evolução futura: um `ERROR_CODES.md`/seção deste documento
listando todos os códigos já emitidos, criado quando o Lote 2 começar a gerar códigos reais por
módulo — não fabricado agora, sem endpoint nenhum ainda existir). Nenhum código é removido depois
de publicado — só marcado não usado.
