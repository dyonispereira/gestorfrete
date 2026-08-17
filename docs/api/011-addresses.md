# 011 — Addresses

Bounded context proprietário: nenhum próprio — `Endereço` é infraestrutura polimórfica
compartilhada (D182/D186), o mesmo padrão físico servindo `crm` (Cliente), `maintenance`
(Fornecedor) e `tenancy` (Filial). Cada endpoint abaixo pertence ao bounded context do **dono**
(D215 continua valendo por chamada — o dono é definido pelo path, nunca ambíguo).

## Achado ao preparar este documento (D231)

`filiais.endereco` (JSONB embutido, existia desde `001-core.md`, antes de `Endereço` existir como
entidade própria) competia com o padrão polimórfico `enderecos` — que D182 sempre pretendeu cobrir
também Filial ("Cliente, Fornecedor e Filial podem ter múltiplos endereços"), mas a migração nunca
foi completada. Corrigido: `filiais.endereco` removida, Filial passa a usar `enderecos` como
Cliente/Fornecedor. Isso **reabre o contrato `Branch` do Lote 2** (`006-branches.md`) — `endereco`
deixa de ser campo embutido, vira sub-recurso `/branches/{id}/addresses`, igual aos demais donos.

## D225 — por que Endereço é um sub-recurso, não um recurso de topo

Não existe `GET /addresses` (coleção geral) nem `POST /addresses` aceitando um `entity_type`
arbitrário no corpo — isso permitiria ao cliente da API associar um endereço a qualquer tipo de
entidade, inclusive fora do conjunto permitido pelo enum físico
(`enderecos_entidade_tipo_enum`, hoje `CLIENTE`/`FORNECEDOR`/`FILIAL`, D231). Em vez disso, três
rotas paralelas, uma por dono — **o dono é implícito no path, nunca um campo que o cliente escolhe**
(D227 — API não cria relacionamentos implícitos inexistentes no domínio; a leitura inversa dessa
regra é: a API também nunca permite ao cliente *inventar* uma associação que o domínio não
autoriza):

```
GET/POST     /api/v1/clients/{id}/addresses
GET/PATCH/DELETE /api/v1/clients/{id}/addresses/{addressId}

GET/POST     /api/v1/suppliers/{id}/addresses
GET/PATCH/DELETE /api/v1/suppliers/{id}/addresses/{addressId}

GET/POST     /api/v1/branches/{id}/addresses
GET/PATCH/DELETE /api/v1/branches/{id}/addresses/{addressId}
```

As três rotas são idênticas em schema/comportamento — documentadas uma única vez aqui
(`Address` completo, distinto do `Address` "de valor" embutido em `components/schemas.md` usado
antes do Lote 3 só como formato de campos de texto; a partir daqui `Address` é um recurso com `id`
próprio) — cada `00N-*.md` de dono só referencia esta seção, nunca redefine.

## Schema `Address` (recurso, substitui o `Address`-valor do Lote 2)

```yaml
Address:
  type: object
  properties:
    id: { $ref: "#/components/schemas/UUID" }
    type:
      type: string
      enum: [PRINCIPAL, COBRANCA, ENTREGA, OUTRO]
      description: "`tipo_endereco` — qualifica o papel deste endereço para o dono."
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

## `GET /{owner}/{id}/addresses`

Lista os endereços do dono (`owner` ∈ `clients`/`suppliers`/`branches`).

**Segurança**: `bearerAuth` + a permissão de **visualização** do dono (`crm.client.view`/
`maintenance.supplier.view`/`tenancy.branch.view`) — **nenhuma permissão própria de Endereço
existe em `RBAC_MATRIX.md`** (D216: nunca inventada aqui). Endereço não tem RBAC independente do
seu dono — faz sentido, ele não existe fora do contexto do dono.

**Responses**

| Código | Corpo |
|---|---|
| `200` | `Pagination` de `Address` (tipicamente poucos itens, sem paginação real na prática, mas o envelope é o mesmo de qualquer coleção, D228) |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `404` | `NotFound` — dono não existe |
| `500` | `InternalServerError` |

## `POST /{owner}/{id}/addresses`

**Segurança**: permissão de **edição** do dono (`crm.client.edit`/`maintenance.supplier.edit`/
`tenancy.branch.edit`).

**Request**

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          type: { type: string, enum: [PRINCIPAL, COBRANCA, ENTREGA, OUTRO] }
          logradouro: { type: string }
          numero: { type: string }
          complemento: { type: string }
          bairro: { type: string }
          cidade: { type: string }
          uf: { type: string, minLength: 2, maxLength: 2 }
          cep: { type: string }
        required: [type, logradouro, bairro, cidade, uf, cep]
```

`entity_type`/`entity_id` **nunca** aparecem no corpo — resolvidos inteiramente do path (`owner` +
`{id}`), nunca aceitos como campo editável (mesmo princípio de D208 aplicado a uma associação de
domínio, não só a tenant).

**Responses**

| Código | Corpo |
|---|---|
| `201` | `Address` criado |
| `400` | `BadRequest` |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `404` | `NotFound` — dono não existe |
| `409` | `Conflict` — `ADDRESS_PRINCIPAL_ALREADY_EXISTS` se `type: PRINCIPAL` e já existir um Principal vigente (`uq_enderecos_entidade_principal`, índice único parcial) |
| `500` | `InternalServerError` |

## `PATCH /{owner}/{id}/addresses/{addressId}`

Mesma segurança/regras de `POST`. `PATCH` altera só os campos enviados (D229).

## `DELETE /{owner}/{id}/addresses/{addressId}`

Soft delete (D219/D177). Mesma segurança de edição do dono.

**Responses adicionais**: `422` — `ADDRESS_CANNOT_DELETE_ONLY_PRINCIPAL` só se o produto decidir
exigir pelo menos um endereço Principal sempre presente (regra de Aplicação/Domínio, não física —
`enderecos` não tem `CHECK` impedindo zero linhas para um dono).

## Como este documento cresce

Se um quarto dono precisar de endereços (nenhum previsto hoje — apenas Cliente/Fornecedor/Filial
têm `entidade_tipo` no enum físico, D231), o enum ganha o novo valor primeiro (Domain/Dictionary/
Relational, D101), só depois a rota `/{novo-dono}/{id}/addresses` é adicionada aqui.
