# 029 — Preventive Maintenance Plans (Planos de Manutenção Preventiva)

Bounded context proprietário: `maintenance` (D215). Reference Data (D036), Aggregate Root próprio —
não é parte do agregado Ordem de Serviço (uma OS `PREVENTIVA` referencia o gatilho que a originou só
por `origin = MANUTENCAO_PREVENTIVA_SUGERIDA`, nunca por FK direta a um Plano).

## `GET /api/v1/planos-manutencao`

**Segurança**: `bearerAuth` + `maintenance.preventive_plan.view`.

**Query parameters**: `page`/`limit`, `vehicle_id` (`veiculo_tracionador_id`), `vehicle_category_id`
(`categoria_veiculo_id`), `trigger_type` (`tipo_gatilho`), `status`.

**Responses**: `200` (`Pagination` de `MaintenancePreventivePlan`, `maintenance-schemas.md`), `401`,
`403`, `500`.

## `GET /api/v1/planos-manutencao/{id}`

**Segurança**: `maintenance.preventive_plan.view`. **Responses**: `200`, `401`, `403`, `404`, `500`.

## `POST /api/v1/planos-manutencao`

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          vehicle_id: { $ref: "components/schemas.md#/UUID" }
          vehicle_category_id: { $ref: "components/schemas.md#/UUID" }
          trigger_type: { type: string, enum: [QUILOMETRAGEM, HORAS_MOTOR, DIAS, CALENDARIO, MOTOR, TELEMETRIA, RECOMENDACAO_FABRICANTE] }
          interval_value: { type: string }
          service_type_id: { $ref: "components/schemas.md#/UUID" }
        required: [trigger_type, interval_value, service_type_id]
```

`vehicle_id`/`vehicle_category_id` — exatamente um dos dois é obrigatório
(`ck_planos_manutencao_preventiva_alvo`) — `400` se nenhum ou os dois forem enviados.

**Segurança**: `maintenance.preventive_plan.create`.

**Responses**: `201` (`MaintenancePreventivePlan`), `400`, `401`, `403`, `404` (Veículo/Categoria/
Tipo de Serviço não existe), `500`.

## `PATCH /api/v1/planos-manutencao/{id}`

D229 — parcial. Inclui `status` (`ATIVO`/`INATIVO`) — diferente da Ordem de Serviço, Plano **não**
tem máquina de estados (é Reference Data simples, D036), então alterar `status` por `PATCH` aqui não
viola D253 (essa regra é específica de Aggregate Roots com transições de negócio).

**Segurança**: `maintenance.preventive_plan.edit`. **Responses**: `200`, `400`, `401`, `403`, `404`,
`500`.

## Sem `DELETE`

`RBAC_MATRIX.md` §7.9 não tem `maintenance.preventive_plan.delete` — mesmo padrão de
`013-cost-centers.md` (Lote 3): desativação via `PATCH status=INATIVO`, nunca reaproveitando `.edit`
para simular uma exclusão (aqui já existe um campo de status que cobre exatamente esse caso, ao
contrário da Ordem de Serviço que precisa de soft delete real por não ter um "status inativo"
equivalente antes de `EM_DIAGNOSTICO`).

## Agenda Preventiva — consulta, não endpoint aqui

`relational/005-manutencao.md` documenta a "Agenda Preventiva" (próxima manutenção prevista por
veículo) como **consulta calculada**, não uma tabela: `valor_intervalo − (leitura_atual −
leitura_no_ultimo_plano_executado)`, cruzando este Plano com `leituras_hodometro`
(`024-odometer-readings.md`, Lote 5). Nenhum endpoint de "agenda" é criado neste lote — calcular essa
projeção é responsabilidade de um endpoint agregador futuro (provável candidato: um relatório/
dashboard em `analytics`, não em `maintenance`), fora de escopo aqui.

## Tipos de Serviço

`tipo_servico_id` é obrigatório para criar um Plano (`tipos_servico`, `relational/005-manutencao.md`)
— sem endpoint próprio, o Plano seria impossível de criar via API. `Tipo de Serviço` já é Reference
Data plenamente especificada (Domain, Dictionary, DDL, RBAC `maintenance.service_type.*`) — exposta
aqui como CRUD mínimo por ser pré-requisito direto deste arquivo, não como entidade nova (ver
"Achados do Lote 6" em `README.md`).

### `GET /api/v1/tipos-servico`

**Segurança**: `maintenance.service_type.view`. **Query parameters**: `page`/`limit`, `search`
(`nome`), `status`. **Responses**: `200` (`Pagination` de `ServiceType`), `401`, `403`, `500`.

### `GET /api/v1/tipos-servico/{id}`

**Responses**: `200`, `401`, `403`, `404`, `500`.

### `POST /api/v1/tipos-servico`

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          name: { type: string }
        required: [name]
```

**Segurança**: `maintenance.service_type.create`. **Responses**: `201` (`ServiceType`), `400`,
`401`, `403`, `409` (D230 — `nome` duplicado no tenant), `500`.

### `PATCH /api/v1/tipos-servico/{id}`

D229 — parcial (`name`, `status`). **Segurança**: `maintenance.service_type.edit`. **Responses**:
`200`, `400`, `401`, `403`, `404`, `409`, `500`.

### Sem `DELETE`

`RBAC_MATRIX.md` não tem `maintenance.service_type.delete` — desativação via `PATCH
status=INATIVO`, mesmo padrão do Plano acima.

## Como este documento cresce

Se `settings`/`administracao` ganhar API própria, a Alçada de Aprovação (`028`) pode passar a
referenciar Tipo de Serviço/categoria para alçadas diferenciadas por tipo de serviço (já citado como
"Requisito futuro" em `003-MANUTENCAO.md`) — nenhuma mudança estrutural aqui, só um novo consumidor
lendo este cadastro.
