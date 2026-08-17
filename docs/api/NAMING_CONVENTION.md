# NAMING_CONVENTION.md — Convenção de Nomenclatura da API

Como todo endpoint é escrito — para que nenhum módulo (Lote 2 em diante) invente sua própria
sintaxe. Aplica-se a toda superfície de `OPENAPI_ARCHITECTURE.md`.

## 1. Recursos são substantivos, no plural, em `kebab-case`

```
GET    /api/v1/viagens
GET    /api/v1/viagens/{id}
POST   /api/v1/viagens
PATCH  /api/v1/viagens/{id}
DELETE /api/v1/viagens/{id}          -- nunca implementado como DELETE físico (D001/D177) — ver seção 5
```

Recurso composto de mais de uma palavra usa `kebab-case`, nunca `camelCase`/`snake_case` no path:

```
GET /api/v1/ordens-servico
GET /api/v1/contas-a-pagar
GET /api/v1/tabelas-preco
```

**Nunca aceito**:

```
GET /Viagens                 -- PascalCase
GET /vehicle-list             -- nome em inglês misturado, não é o nome do recurso real
GET /getViagens                -- verbo no path — REST usa o método HTTP como verbo, não o path
POST /viagens/criar             -- verbo redundante — POST já significa "criar"
```

**Nome do recurso no path é em português para módulos de domínio de negócio**, igual ao vocabulário
já fixado em [`../domain/UBIQUITOUS_LANGUAGE.md`](../domain/UBIQUITOUS_LANGUAGE.md) e usado em toda
a documentação até aqui (`viagens`, não `trips`) — o código interno (bounded contexts, nomes de
classe) usa inglês (D011), a API pública fala a língua do usuário do produto.

**Exceção (D221)**: endpoints de **Core/Identidade/Tenancy** — `auth`, `users`, `roles`,
`permissions`, `branches`, `tenant` — usam paths em **inglês**. Mesmo raciocínio de D011: esses são
conceitos de plataforma/infraestrutura de acesso, não vocabulário de negócio do transportador (o
usuário final do produto pensa em "Motorista"/"Viagem", não em "Role"/"Permission" como conceitos
próprios do seu negócio — são mecanismos do próprio produto). A partir de `Cadastros` (Lote 3 em
diante — Clientes, Fornecedores, Motoristas) e todo módulo de negócio subsequente, o path volta a
ser português. Nenhum outro módulo ganha essa exceção sem decisão explícita — ela existe
especificamente para Core/Identidade/Tenancy, não é um precedente geral para "qualquer coisa que
pareça técnica".

## 2. Sub-recursos (relação de posse, D033) usam nesting — no máximo um nível

```
GET /api/v1/viagens/{id}/ocorrencias
GET /api/v1/viagens/{id}/pontos-parada
GET /api/v1/ordens-servico/{id}/itens
```

Nunca dois níveis de nesting (`/api/v1/viagens/{id}/entregas/{entregaId}/canhotos` não existe) —
quando o sub-recurso também precisa ser acessado isoladamente, ele ganha seu próprio endpoint de
primeiro nível com filtro por FK (ver `FILTERING_SORTING.md`):

```
GET /api/v1/canhotos?entrega_id={id}
```

## 3. Ações que não são CRUD puro (comandos de domínio) são sub-recursos verbais, via `POST`

Nem toda operação é `PATCH` de status — quando a ação é um comando de domínio com nome próprio
(evento já catalogado em [`../product/EVENT_MAP.md`](../product/EVENT_MAP.md)), o endpoint reflete
isso explicitamente, nunca escondido atrás de um `PATCH status=X` genérico:

```
POST /api/v1/viagens/{id}/despachar        -- dispara ViagemDespachada
POST /api/v1/viagens/{id}/encerrar          -- dispara ViagemEncerrada
POST /api/v1/ordens-servico/{id}/aprovar     -- dispara aprovação de custo
POST /api/v1/ctes/{id}/cancelar               -- transição fiscal com regra própria, não um PATCH genérico
```

Critério para decidir `PATCH` genérico vs. comando nomeado: se a transição dispara lógica de
domínio própria (validação de invariante, evento nomeado, side effect em outro bounded context),
vira comando nomeado. Se é só "mudar um campo simples" (ex.: renomear uma Categoria de Veículo),
`PATCH` no recurso basta.

## 4. Parâmetros de path, query string e headers

| Tipo | Convenção | Exemplo |
|---|---|---|
| Parâmetro de path | Nome do identificador, sempre `{id}` para a chave técnica | `/viagens/{id}` |
| Parâmetro de path por código funcional | Quando o endpoint aceita o código legível em vez do UUID (D213) | `/viagens/codigo/{codigo}` — path explícito, nunca ambíguo com `{id}` |
| Query string | `snake_case`, mesmo nome da coluna quando fizer sentido | `?status=ATIVO&data_inicio=2026-07-01` |
| Headers customizados | Prefixo `X-`, `Kebab-Case` | `X-Request-Id`, `X-Correlation-Id`, `X-Tenant-Context` (uso interno/debug, nunca fonte de verdade — D208) |

## 5. Verbos HTTP e o que cada um significa

| Verbo | Uso | Idempotente? |
|---|---|---|
| `GET` | Ler um recurso ou coleção — nunca causa efeito colateral | Sim, sempre |
| `POST` | Criar um recurso, ou executar um comando de domínio nomeado (seção 3) | Não, por padrão — comandos críticos exigem `Idempotency-Key` (`IDEMPOTENCY.md`) |
| `PATCH` | Atualização parcial de um recurso existente | Sim (mesmo corpo, mesmo resultado) |
| `PUT` | **Não usado neste projeto** — toda atualização é parcial por natureza do domínio (nenhuma tela substitui um recurso inteiro de uma vez); evita ambiguidade sobre campos omitidos | — |
| `DELETE` | Aceito na URL por convenção REST, mas **nunca** executa `DELETE` físico no banco — sempre traduzido para soft delete (`excluido_em`/`excluido_por`, D177) pela camada de aplicação | Sim (chamar duas vezes não duplica o efeito) |

## 6. Nomes de campo no corpo JSON

`snake_case`, herdado diretamente do nome da coluna física (`OPENAPI_ARCHITECTURE.md` seção 3) —
sem exceção por endpoint. Campos calculados/somente-leitura (ex.: `viagens.encerrada`, D185) são
expostos com o mesmo nome da coluna `GENERATED`, marcados `readOnly: true` no schema OpenAPI.

## 7. Códigos HTTP — mapeamento padrão

| Código | Quando |
|---|---|
| `200 OK` | Sucesso em `GET`/`PATCH`/comando que não cria recurso |
| `201 Created` | Sucesso em `POST` que cria um recurso — `Location` header aponta para o recurso criado |
| `202 Accepted` | Comando aceito mas processado assincronamente (ex.: exportação de relatório, `exportacoes_geradas`) |
| `204 No Content` | Sucesso em `DELETE` (soft delete aplicado) |
| `400 Bad Request` | Erro de validação de payload — ver `ERROR_MODEL.md` |
| `401 Unauthorized` | Não autenticado |
| `403 Forbidden` | Autenticado, mas RBAC nega (D212) |
| `404 Not Found` | Recurso não existe (ou existe em outro tenant — nunca revela isso, ver `ERROR_MODEL.md`) |
| `409 Conflict` | Conflito de estado (ex.: `Idempotency-Key` reusada com payload diferente, violação de `UNIQUE`) |
| `422 Unprocessable Entity` | Payload sintaticamente válido, mas viola uma regra de negócio (ex.: transição de status inválida) |
| `429 Too Many Requests` | Rate limit excedido (`RATE_LIMITING.md`) |
| `500 Internal Server Error` | Erro interno — nunca expõe stack trace (`ERROR_MODEL.md`) |

## Como este documento cresce

Estável — toda nova rota de módulo (Lote 2 em diante) segue exatamente esta convenção, nunca
inventa uma variação local. Divergência encontrada em revisão de contrato é corrigida aqui primeiro
se for uma regra nova, ou no endpoint se for um erro de aplicação da regra já existente.
