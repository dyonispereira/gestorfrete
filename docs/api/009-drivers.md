# 009 — Drivers

Bounded context proprietário: `drivers` (D215). Entidade central do sistema — mais cuidado aqui
que nos demais cadastros deste lote.

## O que fica fora deste documento (bounded context de outro dono, D215)

- Viagens do Motorista (`viagens.motorista_id`, `alocacoes_recurso_viagem`) — `freight`, entram no
  Lote 4 (`014-trips.md`), nunca um `/drivers/{id}/trips` aqui.
- Adiantamento/Haver do Motorista (`financial.advance`/`financial.driver_balance`, já em
  `RBAC_MATRIX.md`) — `financial`, lote próprio quando Financeiro for modelado na API.
- Assinatura Digital (`assinaturas_digitais`) e Sessão Mobile (`sessoes_mobile`) — `mobile`, lote
  próprio de App Motorista.

## Schema `Driver`

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
    employment_type:
      type: string
      enum: [EMPREGADO, AUTONOMO]
      description: "`tipo_vinculo`."
    fitness_status:
      type: string
      enum: [APTO, BLOQUEADO]
      readOnly: true
      description: "`status_aptidao` — sempre calculado (recalculado quando um Documento do tipo
        CNH muda, `relational/002-cadastros.md`), nunca um campo que o cliente escreve
        diretamente. Não existe `PATCH` de `fitness_status`."
    audit: { $ref: "#/components/schemas/AuditMetadata" }
  required: [id, codigo, nome, cpf, employment_type, fitness_status, audit]
```

## Sub-recurso: Documentos

`documentos_motorista` (D183) — CNH, RG, Exame Toxicológico, Registro ANTT.

```
GET/POST         /api/v1/drivers/{id}/documents
GET/PATCH/DELETE /api/v1/drivers/{id}/documents/{documentId}
```

```yaml
DriverDocument:
  type: object
  properties:
    id: { $ref: "#/components/schemas/UUID" }
    type: { type: string, enum: [CNH, RG, EXAME_TOXICOLOGICO, REGISTRO_ANTT] }
    number: { type: string }
    cnh_category:
      type: string
      nullable: true
      enum: [A, B, C, D, E]
      description: Só preenchido quando `type = CNH` (`ck_documentos_motorista_categoria_so_cnh`).
    expires_at: { type: string, format: date, nullable: true }
    status: { type: string, enum: [VALIDO, VENCIDO], readOnly: true }
    audit: { $ref: "#/components/schemas/AuditMetadata" }
  required: [id, type, number, status, audit]
```

**Segurança de Documentos**: `drivers.driver.view_cnh`/`.edit_cnh` quando `type = CNH`
(criticidade Média, código dedicado em `RBAC_MATRIX.md`); `drivers.driver.view`/`.edit` para os
demais tipos (RG/Exame/ANTT não têm código próprio — D216, nunca inventado). Upload do arquivo
digitalizado usa `drivers.driver.attach`.

## Sub-recurso: nenhum de Endereço/Contato

Motorista **não** está no enum `enderecos_entidade_tipo_enum` (`CLIENTE`/`FORNECEDOR`/`FILIAL`,
D231) — não modelado com múltiplos endereços no Domain Model. Se o produto precisar disso no
futuro, entra pelo Domain primeiro (D101), nunca adicionado aqui como atalho.

## `GET /api/v1/drivers`

**Segurança**: `bearerAuth` + `drivers.driver.view`.

**Query parameters**: `page`/`limit`, `status` (mapeia para `fitness_status`, i.e.
`status_aptidao` — `APTO`/`BLOQUEADO`), `employment_type` (`tipo_vinculo`), `search` (`nome`/`cpf`),
`created_from`/`created_to`.

**Responses**: `200` (`Pagination` de `Driver`), `401`, `403`, `500`.

## `GET /api/v1/drivers/{id}`

**Segurança**: `drivers.driver.view`. **Responses**: `200`, `401`, `403`, `404`
(`DRIVERS_DRIVER_NOT_FOUND`), `500`.

## `GET /api/v1/drivers/me`

Equivalente ao próprio Motorista consultando seu cadastro pelo App — usa `drivers.driver.view_own`
(Escopo "Próprio usuário", D053), resolvido via `usuarios.motorista_id` do ator autenticado (não
via `{id}` na URL). `404` se o Usuário autenticado não tiver `motorista_id` vinculado
(`DRIVERS_NOT_A_DRIVER_ACCOUNT`) — ex.: um Gestor Operacional chamando este endpoint por engano.

**Responses**: `200` (`Driver`), `401`, `404`, `500`.

## `POST /api/v1/drivers`

**Segurança**: `drivers.driver.create`.

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          nome: { type: string }
          cpf: { type: string }
          telefone: { type: string }
          email: { type: string, format: email }
          employment_type: { type: string, enum: [EMPREGADO, AUTONOMO] }
        required: [nome, cpf, employment_type]
```

`fitness_status` nunca aceito no corpo (é `readOnly` — sempre nasce `APTO`, mesmo comportamento do
banco, `status_aptidao NOT NULL DEFAULT 'APTO'`).

**Responses**: `201`, `400`, `401`, `403`, `409` (D230 — `DRIVERS_CPF_ALREADY_EXISTS`,
`uq_motoristas_tenant_id_cpf`), `500`.

## `PATCH /api/v1/drivers/{id}`

**Segurança**: `drivers.driver.edit`. D229 — parcial. `fitness_status` continua não aceito aqui
(é recalculado, nunca escrito diretamente — nem por `PATCH`).

**Responses**: `200`, `400`, `401`, `403`, `404`, `409`, `500`.

## `POST /api/v1/drivers/{id}/block` e `POST /api/v1/drivers/{id}/unblock`

Comandos nomeados (`NAMING_CONVENTION.md` seção 3) — bloqueio/desbloqueio é uma decisão de
segurança/compliance com aprovação própria em `RBAC_MATRIX.md` (Gerente Operacional), não um
`PATCH` genérico de status.

**Segurança**: `drivers.driver.block` / `drivers.driver.unblock`.

**Responses**: `200` (`Driver` atualizado), `401`, `403`, `404`, `422` —
`DRIVERS_ALREADY_BLOCKED`/`DRIVERS_ALREADY_UNBLOCKED`, `500`.

## `DELETE /api/v1/drivers/{id}`

**D219 — soft delete.** **Segurança**: `drivers.driver.delete`.

**Responses**: `204`, `401`, `403`, `404`, `422` — `DRIVERS_DRIVER_HAS_ACTIVE_TRIP` (regra de
Aplicação — Motorista alocado a uma Viagem em andamento, `alocacoes_recurso_viagem` vigente), `500`.

## Histórico — lacuna documentada, não uma tabela inventada

Não existe `motoristas_status_history` nem qualquer tabela de histórico dedicada a Motorista no
Modelo Relacional — diferente de Viagem/CT-e/MDF-e/CIOT (que têm `*_status_history` próprias),
mudança de `fitness_status`/bloqueio de Motorista só fica registrada em `logs_auditoria` (trilha
genérica, D007/D187 — Timeline Universal via `UNION ALL`). Não há endpoint dedicado de "histórico
de Motorista" neste lote — se o produto precisar de uma tela específica para isso, o caminho é
expor uma consulta filtrada sobre `logs_auditoria` (endpoint próprio, fora de `009-drivers.md`),
nunca fabricar uma tabela de histórico que o banco não tem.

## Fora de escopo deste lote

`drivers.driver.export`/`.comment`/`.view_performance` — mesma nota de exportação/comentário
compartilhado dos demais cadastros; "Meu Desempenho" (`view_performance`) depende de indicadores
de `analytics` (D090 — nunca calculado/armazenado em tabela operacional), fora do escopo de CRUD
básico deste lote.

## Como este documento cresce

`Driver` é referenciado por `014-trips.md` (Lote 4) como FK de Viagem — nunca redefinido lá.
