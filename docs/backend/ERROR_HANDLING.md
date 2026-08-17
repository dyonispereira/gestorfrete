# ERROR_HANDLING.md — Exceções e Mapeamento para `docs/api/ERROR_MODEL.md`

## Hierarquia (`core/exceptions/base.py`)

```
ApplicationError (base — code, message, details, http_status)
├── ValidationError            400
├── AuthenticationError         401   ← ver nota abaixo
├── AuthorizationError           403
├── NotFoundError                  404
├── ConflictError                    409
├── DomainError                       422
├── IntegrationError                   502 (default) / 504 (timeout)
└── InfrastructureError                 500
```

Pedido explícito do usuário listava 7 classes (`DomainError`/`ValidationError`/`AuthorizationError`/
`NotFoundError`/`ConflictError`/`IntegrationError`/`InfrastructureError`). **`AuthenticationError`
foi adicionada** — `docs/api/ERROR_MODEL.md` (fonte já congelada, D209) distingue explicitamente
Autenticação (401 — token ausente/inválido/expirado) de Autorização (403 — autenticado mas sem
permissão) como categorias separadas, cada uma com seus próprios `code` de exemplo
(`IDENTITY_INVALID_CREDENTIALS`/`IDENTITY_TOKEN_EXPIRED` vs. `IDENTITY_PERMISSION_DENIED`).
`AuthorizationError` sozinha não tinha como cobrir os dois — mesma disciplina do resto do projeto:
a lista ilustrativa do pedido cede à fonte de verdade já congelada, aditivamente, sem remover nada
do que foi pedido.

`DomainRuleViolationError` (nome já usado na Fase 0) permanece como alias de `DomainError` — nunca
dois nomes divergentes para o mesmo conceito daqui em diante, mas remover o nome antigo agora
quebraria qualquer import futuro escrito contra ele sem necessidade real.

## Construção — `code`/`message` sempre explícitos, nunca hardcoded na classe

```python
raise NotFoundError("FREIGHT_TRIP_NOT_FOUND", "Viagem não encontrada.")
raise DomainError("MAINTENANCE_ORDER_ALREADY_APPROVED", "Ordem de serviço já aprovada.")
```

Cada bounded context levanta com seu próprio `code` (D011 — `SCREAMING_SNAKE_CASE` prefixado pelo
bounded context em inglês) — a classe base nunca fixa um `code` específico, exceto
`InfrastructureError` (default `"INFRASTRUCTURE_ERROR"`) e o handler catch-all
(`"INTERNAL_SERVER_ERROR"`), porque essas duas não pertencem a nenhum bounded context específico.

## Envelope (`core/exceptions/envelope.py`) — idêntico ao `ERROR_MODEL.md`

```python
class ErrorEnvelope(BaseModel):
    error: ErrorBody  # code, message, details: list[ErrorDetail], request_id, correlation_id
```

`request_id`/`correlation_id` vêm de `core.observability.context` (populados pelo
`RequestContextMiddleware` antes de qualquer handler rodar) — nunca fabricados pelo próprio handler
de exceção.

## Os 3 handlers registrados (`core/exceptions/handlers.py`)

| Handler | Dispara para | Log |
|---|---|---|
| `application_error_handler` | Qualquer `ApplicationError` (e subclasses) | `ERROR` se `http_status >= 500`, `INFO` caso contrário — um `NotFoundError` não é um incidente, um `InfrastructureError` é |
| `request_validation_error_handler` | `RequestValidationError` do FastAPI/Pydantic | Sempre — traduz para `VALIDATION_FAILED` + `details` por campo, exatamente o formato de `ERROR_MODEL.md` |
| `unhandled_exception_handler` | Qualquer `Exception` não capturada acima | Sempre `ERROR`, com `exc_info` completo — **mas a resposta ao cliente nunca inclui a mensagem da exceção**, só `"Erro interno do servidor."` |

**Nunca stack trace nem mensagem de exceção crua no corpo da resposta, em nenhum ambiente** — regra
explícita de `ERROR_MODEL.md`, testada diretamente
(`tests/unit/test_exceptions.py::test_unhandled_exception_returns_500_without_leaking_the_exception_message`,
verifica que o texto da exceção literalmente não aparece em lugar nenhum da resposta).

## `Controller` nunca traduz erro de validação manualmente (D214)

`VALIDATION_FAILED` com `details` por campo é gerado automaticamente a partir de
`exc.errors()` do Pydantic — nenhum router escreve essa tradução à mão, mesmo princípio já
registrado no contrato OpenAPI (`ERROR_MODEL.md`: "Gerado automaticamente pela validação Pydantic
do Backend").

## Verificado

`tests/unit/test_exceptions.py` — cada classe mapeada para o `http_status` correto,
`IntegrationError` aceitando `http_status=504` explícito, os 3 handlers exercitados via
`TestClient` contra uma app FastAPI descartável construída só para o teste (nunca contra `main.app`
real, para não acoplar o teste a nenhuma rota de negócio futura).
