# 071 — AI Models (Modelos de IA)

Bounded context proprietário: `ai` (D215). `modelos_ia` — Reference Data, D169: múltiplos modelos
ativos simultaneamente é o esperado, nunca uma exceção.

## D313 — RBAC não existia, corrigido na origem

`ai` não tinha nenhuma seção em `RBAC_MATRIX.md` antes desta preparação — 8 entidades plenamente
especificadas (D161–D172) sem representação alguma, a maior lacuna de bounded context inteiro desta
sprint (empatada com `analytics`/`reporting`, mesma auditoria). Corrigido: nova seção `7.28 ai`
criada, incluindo `ai.model.view`/`.create`/`.edit`, antes de escrever este documento.

## CRUD administrativo restrito

**Segurança de todos os endpoints**: criticidade Alta para escrita — administração de Modelo de IA
é ação sensível (afeta todas as Inferências futuras que o referenciam).

## `GET /api/v1/ai/models`

**Segurança**: `bearerAuth` + `ai.model.view`.

**Query parameters**: `page`/`limit`, `type` (`tipo`), `logical_provider`, `status`.

**Responses**: `200` (`Pagination` de `AIModel`, `ai-schemas.md`), `401`, `403`, `500`.

## `GET /api/v1/ai/models/{id}`

**Responses**: `200` (`AIModel`), `401`, `403`, `404`, `500`.

## `POST /api/v1/ai/models`

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          name: { type: string }
          type: { type: string, enum: [CLASSIFICACAO, PREDICAO, OTIMIZACAO, VISAO_COMPUTACIONAL, GERACAO_DE_TEXTO] }
          version: { type: string }
          logical_provider: { type: string, enum: [INTERNO, PROVEDOR_EXTERNO] }
          capability: { type: string }
          max_context: { type: integer }
        required: [name, type, version, logical_provider, capability]
```

**D170/D309**: `logical_provider` é sempre o conceito lógico (`INTERNO`/`PROVEDOR_EXTERNO`) — este
endpoint **nunca** aceita nome de provedor real (OpenAI/Anthropic/Gemini/Azure/Ollama); a
integração com o provedor de fato é infraestrutura (adapter), fora do domínio e fora deste
contrato.

**Segurança**: `ai.model.create`.

**Responses**: `201` (`AIModel`), `400`, `401`, `403`, `409` (`name`+`version` duplicados,
`uq_modelos_ia_nome_versao`), `500`.

## `PATCH /api/v1/ai/models/{id}`

D229 — parcial (`capability`, `max_context`, `status`). `name`/`type`/`version`/`logical_provider`
não editáveis — trocar a versão de um modelo é criar um novo registro (`uq_modelos_ia_nome_versao`
já modela isso como identidade), nunca reescrever a versão de um existente (mesmo princípio de
D155/D166 — versão sempre nova linha, nunca sobrescrita).

**Segurança**: `ai.model.edit`.

**Responses**: `200` (`AIModel`), `400`, `401`, `403`, `404`, `409`, `500`.

## Sem `DELETE`

`RBAC_MATRIX.md` não tem `ai.model.delete` — descontinuação via `PATCH status=DESCONTINUADO`.
Inferências históricas sempre precisam continuar referenciando o Modelo que as gerou (D166).

## Como este documento cresce

Nenhuma mudança estrutural prevista — o padrão de identidade (`nome`+`versao`) já cobre evolução de
modelo sem exigir novo campo.
