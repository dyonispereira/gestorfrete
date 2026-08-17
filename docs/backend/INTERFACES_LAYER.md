# INTERFACES_LAYER.md — `interfaces/`

A camada mais externa — o único lugar do backend que sabe que existe HTTP/FastAPI. Traduz
requisição em chamada para `application/` e o resultado de volta em resposta HTTP; nunca contém
regra de negócio (D214, já em vigor desde o contrato OpenAPI).

## `interfaces/api/v1/router.py` — composition root de negócio

```python
api_router_v1 = APIRouter(prefix="/api/v1")
# cada bounded context registra seu próprio router aqui, ex.:
#   from modules.freight.interfaces.api.router import freight_router
#   api_router_v1.include_router(freight_router)
```

Vazio nesta etapa (D332 — sem endpoint de negócio sem contrato já implementado). Quando o Lote 2
adicionar o primeiro router real (`identity_access`), ele é incluído aqui, nunca montado
diretamente em `main.py` — `main.py` só conhece `api_router_v1`, nunca um módulo individual.

## `interfaces/api/health.py` — endpoints técnicos

`health_router` — `GET /health`, `/health/live`, `/health/ready`. Deliberadamente **fora** de
`api_router_v1` (fora de `/api/v1`, fora do contrato de negócio congelado) — são infraestrutura, a
exceção explícita que D332 já previa. Detalhe de cada rota em
[`OBSERVABILITY.md`](./OBSERVABILITY.md).

## `interfaces/middlewares/request_context.py` — `RequestContextMiddleware`

Primeiro middleware a rodar (registrado com `app.add_middleware`, que empilha na ordem inversa de
registro — sendo o único middleware nesta etapa, é tanto o mais externo quanto o mais interno).
Resolve `request_id`/`correlation_id` (do header do cliente, quando presente, ou gera um novo),
mede a duração da requisição, emite um log estruturado (`request_completed`/`request_failed`) e
devolve os dois IDs como headers de resposta (`X-Request-Id`/`X-Correlation-Id`). Nunca loga corpo
de requisição/resposta — só metadado.

## `interfaces/dependencies/auth.py` — `get_current_actor`

A dependency que todo router protegido vai declarar (`Depends(get_current_actor)`), implementando o
pipeline de `docs/api/AUTHENTICATION.md` até onde a fundação alcança:

```
Authorization: Bearer <token>
        ↓
HTTPBearer extrai as credenciais (401 IDENTITY_MISSING_CREDENTIALS se ausente)
        ↓
JWTTokenService decodifica (401 IDENTITY_TOKEN_EXPIRED / IDENTITY_INVALID_CREDENTIALS)
        ↓
claims `sub` (user_id) e `tenant_id` extraídos e validados como UUID
        ↓
set_current_tenant_id(tenant_id) — tenant em escopo para toda a requisição
        ↓
yield AuthenticatedActor(user_id, tenant_id)
        ↓ (após a resposta)
reset_current_tenant_id — nunca vaza para a próxima requisição no mesmo worker
```

**O que esta dependency não faz — deliberadamente**: não verifica nenhuma Permissão de
`RBAC_MATRIX.md`. Autenticação (quem é) e Autorização (o que pode fazer) são pipeline steps
distintos em `AUTHENTICATION.md`; RBAC é uma dependency separada, por endpoint, que só nasce quando
o primeiro código de permissão for de fato verificado contra um recurso real (Lote 2). Testado de
ponta a ponta (`tests/unit/test_auth_dependency.py`) contra uma rota descartável criada só para o
teste — nenhuma rota de negócio real depende disso ainda.

## Schemas Pydantic (`interfaces/schemas/`, por módulo)

Cada bounded context terá seus próprios schemas de request/response, espelhando exatamente os
schemas já definidos em `docs/api/openapi.yaml`/`docs/api/components/*.md` (D332 — o Backend
implementa o contrato, nunca o inverso). Nenhum schema genérico existe na fundação por essa razão:
schema de interface é, por definição, específico do contrato de cada endpoint já congelado.

## Como esta camada cresce

Primeiro router real: `modules/identity_access/interfaces/api/` no Sprint 11 Lote 2, implementando
`001-authentication.md`/`003-users.md` exatamente como já especificados no contrato congelado.
