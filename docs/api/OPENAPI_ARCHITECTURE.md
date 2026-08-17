# OPENAPI_ARCHITECTURE.md — Arquitetura da API

Primeiro documento da Sprint 10. Define como Frontend, App Motorista, integrações externas e
webhooks conversam com o Backend — o contrato vem antes da implementação (D210), nunca o contrário.
Nenhum endpoint de negócio é definido aqui — isso é Lote 2 em diante. Este documento é a fundação
que todo endpoint futuro vai obedecer.

## 1. Padrão de protocolo

| Item | Decisão |
|---|---|
| Especificação | **OpenAPI 3.1** — alinhada a JSON Schema (permite reuso direto dos tipos Pydantic do backend na geração do contrato) |
| Estilo arquitetural | **REST** sobre HTTP — não GraphQL, não RPC puro. Justificativa: o domínio já é modelado como agregados/recursos (Domain Model, 175 entidades) — REST mapeia diretamente para isso; GraphQL resolveria um problema (under/over-fetching) que este produto não tem hoje (telas são conhecidas antecipadamente, não ad-hoc) |
| Formato de payload | **JSON**, sempre — nenhum endpoint aceita/retorna XML, `multipart/form-data` só para upload de arquivo (anexos, D024) |
| Codificação | **UTF-8**, sempre — `Content-Type: application/json; charset=utf-8` |
| Transporte | **HTTPS obrigatório** em todo ambiente além de Development local — nunca HTTP puro, mesmo internamente (D005/D006 exigem que o isolamento de tenant nunca dependa só da rede ser "confiável") |
| API Gateway | Ponto único de entrada na frente do serviço FastAPI — responsável por TLS termination, rate limiting (`RATE_LIMITING.md`), roteamento por versão (`VERSIONING.md`); a escolha do produto de Gateway (Kong/AWS API Gateway/Nginx+custom/etc.) é decisão de infraestrutura, não de contrato — não fixada aqui |

## 2. Um serviço, múltiplas superfícies

**Não criamos APIs fisicamente separadas para cada consumidor** — um único serviço FastAPI, um único
contrato OpenAPI versionado (D207), organizado por `tags`/routers. A separação abaixo é lógica
(autenticação, escopo de rate limit, público-alvo), não uma duplicação de endpoints:

| Superfície | Quem consome | Autenticação (ver `AUTHENTICATION.md`) | Observação |
|---|---|---|---|
| **API do ERP Web** | Frontend Next.js, uso interativo do usuário da transportadora | Sessão/token de browser | Superfície mais ampla — cobre praticamente todos os módulos do Domain Model |
| **API do App Motorista** | App mobile do Motorista | Access Token + Refresh Token | Subconjunto de endpoints (os que o Motorista realmente usa — `flows/002-VIAGEM.md` etc.), mesma versão de contrato, mesmos schemas |
| **API Pública** | Integrações de terceiros (parceiros, ERPs externos do cliente) — **não implementada nesta sprint**, documentada como superfície reservada | API Key / Client Credential | Subconjunto deliberadamente pequeno e estável (D213 — nunca expõe estrutura interna desnecessária); versionamento ainda mais rígido que as demais superfícies, porque mudanças quebram código de terceiros que a equipe não controla |
| **API Interna** | Serviço a serviço, automações administrativas da própria plataforma GestorFrete (equipe interna, `RBAC_MATRIX.md` seção 7.26) | API Key / Client Credential com escopo administrativo | Nunca exposta ao tenant — endpoints cross-tenant (auditoria de compliance, suporte) vivem aqui |
| **Webhooks** | Sistemas do tenant recebendo eventos do GestorFrete | Assinatura HMAC (`WEBHOOKS.md`) | Direção invertida — o GestorFrete é quem chama, não quem recebe |

Uma superfície nova só é criada quando o público/autenticação/rate-limit realmente exigem algo
diferente — nunca "porque parece mais organizado" (mesmo princípio de D076 aplicado à arquitetura
de API).

## 3. Padrão de resposta

**Recurso único**: retornado diretamente, sem envelope:

```json
{
  "id": "a1b2c3d4-...",
  "codigo": "VG-2026-000123",
  "status": "EM_ANDAMENTO"
}
```

**Coleção**: envelope com `data` + `meta` — nunca um array puro na raiz (impede adicionar metadados
depois sem quebrar contrato):

```json
{
  "data": [ { "id": "...", "codigo": "..." } ],
  "meta": {
    "pagination": { "...": "ver PAGINATION.md" }
  }
}
```

**Erro**: envelope próprio, nunca misturado com o formato de sucesso — ver `ERROR_MODEL.md`.

**Nomenclatura de campos JSON**: `snake_case`, igual às colunas do banco (`tenant_id`,
`data_programada`, `criado_em`) — nenhuma camada de tradução `camelCase`↔`snake_case` entre
Pydantic/SQLAlchemy e o payload HTTP. Motivo: o backend já usa Python (convenção `snake_case`
nativa) e o schema Pydantic é gerado a partir do mesmo modelo que lê o banco — forçar `camelCase`
no payload exigiria uma camada de mapeamento em toda rota, sem benefício real (o Frontend em
TypeScript consome ambos os estilos com igual facilidade).

## 4. Cabeçalhos obrigatórios (toda requisição/resposta)

| Cabeçalho | Direção | Propósito |
|---|---|---|
| `Authorization` | Requisição | Token de autenticação (`AUTHENTICATION.md`) |
| `X-Request-Id` | Requisição (opcional, gerado se ausente) / Resposta (sempre) | Identifica uma única chamada HTTP — usado em log técnico, correlacionado no `error.request_id` (`ERROR_MODEL.md`) |
| `X-Correlation-Id` | Requisição (opcional) / Resposta (sempre) | Agrupa múltiplas chamadas/eventos de uma mesma transação de negócio — **mesmo conceito físico de `logs_auditoria.id_correlacao`** (D147/`AUDIT_MODEL.md`); se o cliente não enviar, o Backend gera um novo e o devolve, para que toda a cadeia de efeitos daquela ação (ex.: uma transição de Viagem que dispara `financial`/`documents`) compartilhe o mesmo identificador |
| `Idempotency-Key` | Requisição (obrigatório para comandos críticos) | Ver `IDEMPOTENCY.md` (D211) |
| `Content-Type` | Ambos | Sempre `application/json; charset=utf-8` (exceto upload) |

`X-Request-Id` ≠ `X-Correlation-Id`: o primeiro é por chamada HTTP, o segundo é por transação de
negócio (pode abranger várias chamadas HTTP e eventos assíncronos). Confundir os dois foi um erro
comum o suficiente em outros projetos para merecer a distinção explícita aqui.

## 5. Tenant, RBAC e Domínio — pipeline de toda requisição autenticada

```
Requisição chega
      │
      ▼
Autenticação (AUTHENTICATION.md) — quem é o ator (Usuário, Motorista, Client/API Key)
      │
      ▼
Tenant resolvido do contexto autenticado — NUNCA do body/query/path (D208)
      │
      ▼
RBAC avaliado (RBAC_MATRIX.md, mesma matriz, sem exceção — D212) — o ator tem a Permissão
      │  necessária, no Escopo (D053) necessário, para esta ação?
      ▼
Controller/rota delega para Application (casos de uso) — nunca contém regra de negócio nem SQL
      │  direto (D214)
      ▼
Domain executa a regra; Infrastructure persiste
```

Nenhuma camada acima é opcional ou contornável por um endpoint específico — um endpoint que
"esquece" de checar RBAC é um bug de implementação, não uma exceção de design.

## 6. Referências

| Assunto | Documento |
|---|---|
| Nomenclatura de endpoints/recursos | [`NAMING_CONVENTION.md`](./NAMING_CONVENTION.md) |
| Versionamento | [`VERSIONING.md`](./VERSIONING.md) |
| Autenticação | [`AUTHENTICATION.md`](./AUTHENTICATION.md) |
| Erros | [`ERROR_MODEL.md`](./ERROR_MODEL.md) |
| Paginação | [`PAGINATION.md`](./PAGINATION.md) |
| Filtros e ordenação | [`FILTERING_SORTING.md`](./FILTERING_SORTING.md) |
| Idempotência | [`IDEMPOTENCY.md`](./IDEMPOTENCY.md) |
| Rate limiting | [`RATE_LIMITING.md`](./RATE_LIMITING.md) |
| Webhooks | [`WEBHOOKS.md`](./WEBHOOKS.md) |

## Como este documento cresce

Estável como fundação — mudanças aqui afetam toda superfície de API, então exigem revisão explícita
(mesmo cuidado de "arquitetura congelada" já aplicado a `docs/domain/`, ver memória de processo).
Endpoints de módulos específicos (Lote 2 em diante) referenciam este documento, nunca o reescrevem.
