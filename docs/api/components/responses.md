# components/responses.md — Respostas Reutilizáveis

Todo endpoint referencia estas respostas para os códigos comuns — nunca redefine o corpo de um
`401`/`403`/`404` localmente (mesmo princípio de não duplicação de `schemas.md`). Implementação
real em `openapi.yaml` `#/components/responses/*`.

## Sucesso (não compartilhado — cada endpoint define seu próprio corpo de sucesso)

`200`/`201`/`202`/`204` sempre retornam o schema específico do recurso (`schemas.md`) — não há um
"sucesso genérico" reutilizável, porque o corpo muda por endpoint. O que é comum e reutilizável é a
**estrutura do envelope** (`OPENAPI_ARCHITECTURE.md` seção 3: objeto direto para recurso único,
`{data, meta}` para coleção via `Pagination`, `schemas.md`).

## Erros (compartilhados por toda a API)

### `BadRequest` (400)

```yaml
BadRequest:
  description: Payload sintaticamente inválido — ver ERROR_MODEL.md.
  content:
    application/json:
      schema:
        $ref: "#/components/schemas/ValidationError"
      example:
        error:
          code: "VALIDATION_FAILED"
          message: "Um ou mais campos são inválidos."
          details:
            - field: "email"
              code: "REQUIRED"
              message: "Campo obrigatório."
          request_id: "a1b2c3d4-..."
```

### `Unauthorized` (401)

```yaml
Unauthorized:
  description: Não autenticado — token ausente, inválido ou expirado.
  content:
    application/json:
      schema:
        $ref: "#/components/schemas/Error"
      example:
        error:
          code: "IDENTITY_TOKEN_EXPIRED"
          message: "Sessão expirada. Faça login novamente."
          details: []
          request_id: "a1b2c3d4-..."
```

### `Forbidden` (403)

```yaml
Forbidden:
  description: Autenticado, mas sem a Permissão/Escopo necessário (RBAC, D212). Cada endpoint
    declara em `security.md` qual código de RBAC_MATRIX.md é exigido.
  content:
    application/json:
      schema:
        $ref: "#/components/schemas/Error"
      example:
        error:
          code: "IDENTITY_PERMISSION_DENIED"
          message: "Você não tem permissão para executar esta ação."
          details: []
          request_id: "a1b2c3d4-..."
```

### `NotFound` (404)

```yaml
NotFound:
  description: Recurso não existe, ou existe em outro tenant — nunca 403 nesse segundo caso
    (ERROR_MODEL.md, evita revelar existência entre tenants).
  content:
    application/json:
      schema:
        $ref: "#/components/schemas/Error"
      example:
        error:
          code: "IDENTITY_USER_NOT_FOUND"
          message: "Usuário não encontrado."
          details: []
          request_id: "a1b2c3d4-..."
```

### `Conflict` (409)

```yaml
Conflict:
  description: Conflito de estado — UNIQUE violado, ou Idempotency-Key reusada com payload
    diferente (IDEMPOTENCY.md).
  content:
    application/json:
      schema:
        $ref: "#/components/schemas/Error"
      example:
        error:
          code: "IDENTITY_EMAIL_ALREADY_EXISTS"
          message: "Já existe um usuário com este e-mail neste tenant."
          details: []
          request_id: "a1b2c3d4-..."
```

### `UnprocessableEntity` (422)

```yaml
UnprocessableEntity:
  description: Payload válido, mas viola uma regra de negócio.
  content:
    application/json:
      schema:
        $ref: "#/components/schemas/Error"
      example:
        error:
          code: "IDENTITY_ROLE_IN_USE"
          message: "Papel não pode ser excluído enquanto estiver atribuído a um usuário."
          details: []
          request_id: "a1b2c3d4-..."
```

### `TooManyRequests` (429)

```yaml
TooManyRequests:
  description: Rate limit excedido (RATE_LIMITING.md).
  headers:
    Retry-After:
      schema: { type: integer }
      description: Segundos até a próxima tentativa fazer sentido.
  content:
    application/json:
      schema:
        $ref: "#/components/schemas/Error"
      example:
        error:
          code: "RATE_LIMIT_EXCEEDED"
          message: "Limite de requisições excedido. Tente novamente em instantes."
          details: []
          request_id: "a1b2c3d4-..."
```

### `InternalServerError` (500)

```yaml
InternalServerError:
  description: Erro interno — nunca expõe stack trace ou detalhe de implementação (ERROR_MODEL.md).
  content:
    application/json:
      schema:
        $ref: "#/components/schemas/Error"
      example:
        error:
          code: "INTERNAL_SERVER_ERROR"
          message: "Ocorreu um erro inesperado. Nossa equipe foi notificada."
          details: []
          request_id: "a1b2c3d4-..."
```

## Qual endpoint usa qual resposta

| Resposta | Usada por |
|---|---|
| `BadRequest` | Todo `POST`/`PATCH` |
| `Unauthorized` | Todo endpoint protegido (todos deste lote, exceto `POST /auth/login` e `POST /auth/forgot-password`) |
| `Forbidden` | Todo endpoint com RBAC (todos exceto os de `001-authentication.md`, que só exigem autenticação, não uma Permissão específica) |
| `NotFound` | Todo `GET`/`PATCH`/`DELETE` por `{id}` |
| `Conflict` | Todo `POST`/`PATCH` que viola `UNIQUE` (e-mail duplicado, código duplicado) |
| `UnprocessableEntity` | Toda regra de negócio (ex.: excluir Papel em uso) |
| `TooManyRequests` | Toda rota, mas com política diferenciada — `RATE_LIMITING.md`, especialmente agressiva em `POST /auth/login` |
| `InternalServerError` | Toda rota |

## Como este documento cresce

Nenhuma resposta nova é criada por endpoint específico sem antes verificar se já existe uma
resposta genérica aqui que sirva — só um novo `error.code` dentro do schema `Error` já existente,
nunca uma nova estrutura de resposta paralela.
