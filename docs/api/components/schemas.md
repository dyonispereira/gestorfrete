# components/schemas.md — Schemas Reutilizáveis

Todo schema aqui é referenciado (`$ref`) pelos endpoints — nunca duplicado inline em um documento de
módulo (D069-style, mesmo princípio de não duplicação já aplicado à camada de banco). Implementação
real vive em `openapi.yaml` `#/components/schemas/*`; este arquivo é a documentação legível do
mesmo conteúdo, sempre sincronizada com o YAML (nunca a fonte diverge da outra).

**D217 — nenhum schema abaixo é uma cópia direta de tabela SQL.** Cada um passou por
Tabela → Domain → DTO: colunas internas (`senha_hash`, `excluido_em`, `excluido_por`, `tenant_id`
redundante) nunca aparecem em resposta de API.

## Primitivos

### `UUID`

```yaml
UUID:
  type: string
  format: uuid
  example: "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d"
```

### `Timestamp`

```yaml
Timestamp:
  type: string
  format: date-time
  description: Sempre TIMESTAMPTZ em UTC na serialização (TIMESTAMP_STRATEGY.md) — conversão para
    fuso do tenant é responsabilidade do Frontend, nunca da API.
  example: "2026-07-30T14:32:00Z"
```

### `Money`

```yaml
Money:
  type: object
  description: Reutilizado a partir do Lote 3 (nenhum recurso deste lote tem campo monetário) —
    implementação física de D075 (NUMERIC(14,2), moeda BRL implícita).
  properties:
    amount:
      type: string
      description: Decimal como string, nunca float (evita erro de arredondamento binário) —
        mesmo cuidado de NUMERIC(14,2) no banco.
      example: "1250.50"
    currency:
      type: string
      enum: ["BRL"]
      default: "BRL"
      description: Hoje sempre BRL (D075) — campo existe para expansão futura, mesmo motivo já
        registrado na camada de banco.
  required: [amount, currency]
```

### `AddressFields`

```yaml
AddressFields:
  type: object
  description: Só os campos de texto de um endereço, sem identidade própria — usado quando um
    endereço aparece embutido em snapshot (ex.: `viagens.cliente_snapshot`), nunca como recurso
    editável isoladamente. Para o recurso Endereço completo (com `id`, `type`, ciclo de vida
    próprio via `/{owner}/{id}/addresses`), ver `Address` em `../011-addresses.md` (D231 — Lote 3
    promoveu Endereço de "campo embutido do dono" a sub-recurso compartilhado; `Branch` não usa
    mais este schema desde então).
  properties:
    logradouro: { type: string }
    numero: { type: string, nullable: true }
    complemento: { type: string, nullable: true }
    bairro: { type: string }
    cidade: { type: string }
    uf: { type: string, minLength: 2, maxLength: 2 }
    cep: { type: string }
  required: [logradouro, bairro, cidade, uf, cep]
```

## Paginação

### `PageMeta`

```yaml
PageMeta:
  type: object
  description: "Ver PAGINATION.md — este lote usa só Offset (Master Data), nenhum recurso é Time
    Series/History."
  properties:
    page: { type: integer, minimum: 1 }
    limit: { type: integer, minimum: 1, maximum: 100 }
    total_items: { type: integer, minimum: 0 }
    total_pages: { type: integer, minimum: 0 }
  required: [page, limit, total_items, total_pages]
```

### `Pagination`

```yaml
Pagination:
  type: object
  description: Envelope de coleção — nunca um array puro na raiz (OPENAPI_ARCHITECTURE.md seção 3).
  properties:
    data:
      type: array
      items: {}   # cada endpoint substitui por seu schema de item específico
    meta:
      type: object
      properties:
        pagination:
          $ref: "#/components/schemas/PageMeta"
  required: [data, meta]
```

## Erros

### `Error`

```yaml
Error:
  type: object
  description: Ver ERROR_MODEL.md — envelope único de toda a API, D209.
  properties:
    error:
      type: object
      properties:
        code: { type: string, example: "IDENTITY_USER_NOT_FOUND" }
        message: { type: string, example: "Usuário não encontrado." }
        details:
          type: array
          items:
            $ref: "#/components/schemas/ValidationErrorDetail"
        request_id: { type: string, format: uuid }
        correlation_id: { type: string, format: uuid }
      required: [code, message, details, request_id]
  required: [error]
```

### `ValidationError`

```yaml
ValidationError:
  allOf:
    - $ref: "#/components/schemas/Error"
  description: Especialização de Error para 400 — `details` sempre populado (ERROR_MODEL.md).
```

### `ValidationErrorDetail`

```yaml
ValidationErrorDetail:
  type: object
  properties:
    field: { type: string, example: "email" }
    code: { type: string, example: "REQUIRED" }
    message: { type: string, example: "Campo obrigatório." }
  required: [field, code, message]
```

## Auditoria e contexto

### `AuditMetadata`

```yaml
AuditMetadata:
  type: object
  description: Auditoria leve (AUDIT_MODEL.md) exposta como objeto aninhado — nunca as 4 colunas
    soltas na raiz do recurso (D217, evita que o schema pareça uma cópia 1:1 da tabela).
  properties:
    created_at:
      $ref: "#/components/schemas/Timestamp"
    created_by:
      $ref: "#/components/schemas/UUID"
      nullable: true
      description: Nulo quando a ação foi automática/sistema.
    updated_at:
      $ref: "#/components/schemas/Timestamp"
    updated_by:
      $ref: "#/components/schemas/UUID"
      nullable: true
  required: [created_at, updated_at]
```

Nunca inclui `excluido_em`/`excluido_por` — soft delete é mecanismo interno (D177); um recurso
excluído logicamente não é retornado por `GET` normal (mesmo filtro `WHERE excluido_em IS NULL` já
usado em todo índice, `INDEXES.md` categoria 10), então a API nunca precisa expressar esse estado
ao cliente através deste objeto.

### `TenantContext`

```yaml
TenantContext:
  type: object
  description: Resumo do tenant do ator autenticado — embutido em GET /auth/me, nunca o schema
    completo de Tenant (esse fica em GET /tenant, 002-tenants.md). Nunca aceito como parâmetro de
    entrada em nenhum endpoint (D208/D218) — só aparece em resposta.
  properties:
    id:
      $ref: "#/components/schemas/UUID"
    codigo: { type: string, example: "TRANSP-001" }
    razao_social: { type: string }
    status: { type: string, enum: [TRIAL, ATIVO, SUSPENSO, CANCELADO] }
  required: [id, codigo, razao_social, status]
```

## Entidades deste lote

### `User`

```yaml
User:
  type: object
  properties:
    id: { $ref: "#/components/schemas/UUID" }
    codigo: { type: string, example: "USR-000123" }
    nome: { type: string }
    email: { type: string, format: email }
    status: { type: string, enum: [ATIVO, INATIVO, BLOQUEADO] }
    driver_id:
      $ref: "#/components/schemas/UUID"
      nullable: true
      description: Vínculo opcional a Motorista (D029) — no máximo um dos dois (driver_id/
        employee_id) preenchido.
    employee_id:
      $ref: "#/components/schemas/UUID"
      nullable: true
    roles:
      type: array
      items: { $ref: "#/components/schemas/UUID" }
      description: IDs dos Papéis atribuídos — GET /users/{id} expande para RoleSummary
        (id + nome) quando `?expand=roles` for usado (FILTERING_SORTING.md).
    audit: { $ref: "#/components/schemas/AuditMetadata" }
  required: [id, codigo, nome, email, status, audit]
```

Nunca inclui `senha_hash` (nem em nenhum campo com outro nome) — não há rota que devolva o hash de
senha em nenhuma circunstância, nem para o próprio usuário autenticado.

### `Role`

```yaml
Role:
  type: object
  properties:
    id: { $ref: "#/components/schemas/UUID" }
    codigo: { type: string, example: "ROLE-GESTOR-OP" }
    nome: { type: string, example: "Gestor Operacional" }
    descricao: { type: string, nullable: true }
    permissions:
      type: array
      items: { type: string, example: "identity_access.user.view" }
      description: Códigos de Permissão associados (papel_permissao) — sempre códigos já
        existentes em RBAC_MATRIX.md (D216), nunca criados aqui.
    audit: { $ref: "#/components/schemas/AuditMetadata" }
  required: [id, codigo, nome, permissions, audit]
```

### `Permission`

```yaml
Permission:
  type: object
  description: Platform Reference Data (D046) — somente leitura para clientes normais.
  properties:
    id: { $ref: "#/components/schemas/UUID" }
    code: { type: string, example: "identity_access.user.view" }
    name: { type: string, example: "Visualizar usuário" }
    module: { type: string, example: "identity_access" }
  required: [id, code, name, module]
```

### `Branch`

```yaml
Branch:
  type: object
  description: "`endereco` não é mais um campo deste schema (D231, Lote 3) — endereço de Filial é
    sub-recurso (`GET /branches/{id}/addresses`, `../011-addresses.md`), igual a Cliente/Fornecedor."
  properties:
    id: { $ref: "#/components/schemas/UUID" }
    codigo: { type: string, example: "FIL-SP-001" }
    nome: { type: string }
    is_headquarters:
      type: boolean
      description: "`esta_matriz` na base — no máximo uma Filial com este valor `true` por tenant
        (constraint física, CONSTRAINTS.md)."
    audit: { $ref: "#/components/schemas/AuditMetadata" }
  required: [id, codigo, nome, is_headquarters, audit]
```

### `Client`

```yaml
Client:
  type: object
  properties:
    id: { $ref: "#/components/schemas/UUID" }
    codigo: { type: string, example: "CLI-000456" }
    razao_social: { type: string }
    nome_fantasia: { type: string, nullable: true }
    document: { type: string }
    telefone: { type: string, nullable: true }
    email: { type: string, format: email, nullable: true }
    status: { type: string, enum: [ATIVO, INATIVO] }
    audit: { $ref: "#/components/schemas/AuditMetadata" }
  required: [id, codigo, razao_social, document, status, audit]
```

### `Supplier`

```yaml
Supplier:
  type: object
  properties:
    id: { $ref: "#/components/schemas/UUID" }
    codigo: { type: string, example: "FOR-000789" }
    razao_social: { type: string }
    cnpj: { type: string }
    telefone: { type: string, nullable: true }
    category:
      type: string
      nullable: true
      enum: [PECA, RECAPAGEM, SEGURO, OFICINA, POSTO, BORRACHARIA, GUINCHO, OUTRO]
    status: { type: string, enum: [ATIVO, INATIVO] }
    audit: { $ref: "#/components/schemas/AuditMetadata" }
  required: [id, codigo, razao_social, cnpj, status, audit]
```

### `Driver`

```yaml
Driver:
  type: object
  properties:
    id: { $ref: "#/components/schemas/UUID" }
    codigo: { type: string, example: "MOT-000321" }
    nome: { type: string }
    cpf: { type: string }
    telefone: { type: string, nullable: true }
    email: { type: string, format: email, nullable: true }
    employment_type: { type: string, enum: [EMPREGADO, AUTONOMO] }
    fitness_status: { type: string, enum: [APTO, BLOQUEADO], readOnly: true }
    audit: { $ref: "#/components/schemas/AuditMetadata" }
  required: [id, codigo, nome, cpf, employment_type, fitness_status, audit]
```

### `DriverDocument`

```yaml
DriverDocument:
  type: object
  properties:
    id: { $ref: "#/components/schemas/UUID" }
    type: { type: string, enum: [CNH, RG, EXAME_TOXICOLOGICO, REGISTRO_ANTT] }
    number: { type: string }
    cnh_category: { type: string, nullable: true, enum: [A, B, C, D, E] }
    expires_at: { type: string, format: date, nullable: true }
    status: { type: string, enum: [VALIDO, VENCIDO], readOnly: true }
    audit: { $ref: "#/components/schemas/AuditMetadata" }
  required: [id, type, number, status, audit]
```

### `Employee`

```yaml
Employee:
  type: object
  properties:
    id: { $ref: "#/components/schemas/UUID" }
    codigo: { type: string, example: "FUNC-000045" }
    nome: { type: string }
    cargo: { type: string }
    hired_at: { type: string, format: date, nullable: true }
    status: { type: string, enum: [ATIVO, INATIVO] }
    audit: { $ref: "#/components/schemas/AuditMetadata" }
  required: [id, codigo, nome, cargo, status, audit]
```

### `Address` (recurso — D231, substitui o embutido do Lote 2)

```yaml
Address:
  type: object
  description: Sub-recurso de Cliente/Fornecedor/Filial (../011-addresses.md) — não confundir com
    `AddressFields`, que é só o formato de texto sem identidade própria.
  properties:
    id: { $ref: "#/components/schemas/UUID" }
    type: { type: string, enum: [PRINCIPAL, COBRANCA, ENTREGA, OUTRO] }
    logradouro: { type: string }
    numero: { type: string, nullable: true }
    complemento: { type: string, nullable: true }
    bairro: { type: string }
    cidade: { type: string }
    uf: { type: string, minLength: 2, maxLength: 2 }
    cep: { type: string }
    audit: { $ref: "#/components/schemas/AuditMetadata" }
  required: [id, type, logradouro, bairro, cidade, uf, cep, audit]
```

### `Contact`

```yaml
Contact:
  type: object
  description: Sub-recurso exclusivo de Cliente (../012-contacts.md) — sem created_by/updated_by,
    `contatos_cliente` não tem essas colunas.
  properties:
    id: { $ref: "#/components/schemas/UUID" }
    nome: { type: string }
    cargo: { type: string, nullable: true }
    telefone: { type: string, nullable: true }
    email: { type: string, format: email, nullable: true }
    created_at: { $ref: "#/components/schemas/Timestamp" }
    updated_at: { $ref: "#/components/schemas/Timestamp" }
  required: [id, nome, created_at, updated_at]
```

### `CostCenter`

```yaml
CostCenter:
  type: object
  properties:
    id: { $ref: "#/components/schemas/UUID" }
    codigo: { type: string, example: "CC-000012" }
    accounting_code: { type: string }
    nome: { type: string }
    branch_id: { $ref: "#/components/schemas/UUID", nullable: true }
    status: { type: string, enum: [ATIVO, INATIVO] }
    audit: { $ref: "#/components/schemas/AuditMetadata" }
  required: [id, codigo, accounting_code, nome, status, audit]
```

### `Tenant`

```yaml
Tenant:
  type: object
  description: GET/PATCH /tenant sempre resolve para o tenant do contexto autenticado (D208) —
    nunca aceita um identificador de tenant diferente na URL.
  properties:
    id: { $ref: "#/components/schemas/UUID" }
    codigo: { type: string }
    razao_social: { type: string }
    cnpj: { type: string }
    status: { type: string, enum: [TRIAL, ATIVO, SUSPENSO, CANCELADO], readOnly: true }
    audit: { $ref: "#/components/schemas/AuditMetadata" }
  required: [id, codigo, razao_social, cnpj, status, audit]
```

`status` é `readOnly` — transição de status do Tenant é governada pelo fluxo de assinatura/
cobrança (`flows/001-ONBOARDING.md`), nunca um `PATCH` direto de cliente (`PATCH /tenant` só altera
`razao_social`/`cnpj`, nunca `status`).

### `Session`

```yaml
Session:
  type: object
  description: Resumo de sessão de acesso — exposto em GET /auth/me (sessão atual), nunca uma
    listagem de todas as sessões neste lote (fora de escopo, ver 001-authentication.md).
  properties:
    id: { $ref: "#/components/schemas/UUID" }
    started_at: { $ref: "#/components/schemas/Timestamp" }
    expires_at: { $ref: "#/components/schemas/Timestamp" }
    status: { type: string, enum: [ATIVA, EXPIRADA, ENCERRADA] }
  required: [id, started_at, expires_at, status]
```

## Como este documento cresce

Todo schema novo (Lote 3 em diante) é adicionado aqui antes de ser referenciado em qualquer
endpoint — nunca definido inline num único documento de módulo. `Money`/`Address`/`Timestamp`/
`UUID`/`Pagination`/`Error`/`AuditMetadata` já estão prontos para reuso imediato no Lote 3
(Cadastros).
