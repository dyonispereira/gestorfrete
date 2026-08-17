# 052 — Geofences (Cercas Eletrônicas)

Bounded context proprietário: `tracking` (D215). `cercas_eletronicas` — Configuração/Reference Data
(D036/D122), **não** histórico (D289): CRUD completo aqui; eventos de entrada/saída pertencem a
`051-tracking-events.md`, nunca a este cadastro.

## `GET /api/v1/tracking/geofences`

**Segurança**: `bearerAuth` + `tracking.geofence.view`.

**Query parameters**: `page`/`limit`, `search` (`nome`), `geometry_type` (`tipo_geometria`),
`client_id` (`cliente_id`), `branch_id` (`filial_id`), `status`.

**Responses**: `200` (`Pagination` de `Geofence`, `tracking-schemas.md`), `401`, `403`, `500`.

## `GET /api/v1/tracking/geofences/{id}`

**Responses**: `200` (`Geofence`), `401`, `403`, `404`, `500`.

## `POST /api/v1/tracking/geofences`

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          name: { type: string }
          geometry_type: { type: string, enum: [CIRCULO, POLIGONO] }
          center: { $ref: "components/tracking-schemas.md#/GeoPoint" }
          radius_meters: { type: number }
          polygon:
            type: array
            items: { $ref: "components/tracking-schemas.md#/GeoPoint" }
          client_id: { $ref: "components/schemas.md#/UUID" }
          branch_id: { $ref: "components/schemas.md#/UUID" }
        required: [name, geometry_type]
```

`geometry_type = CIRCULO` exige `center`+`radius_meters`; `geometry_type = POLIGONO` exige
`polygon` (mínimo 3 pontos) — `ck_cercas_eletronicas_geometria` — `400` caso contrário.

**Segurança**: `tracking.geofence.create`.

**Responses**: `201` (`Geofence`), `400`, `401`, `403`, `404` (Cliente/Filial não existe), `409` —
`nome` duplicado no tenant, `500`.

## `PATCH /api/v1/tracking/geofences/{id}`

D229 — parcial. Trocar `geometry_type` exige enviar os campos de geometria correspondentes ao novo
tipo (mesma validação do `POST`).

**Segurança**: `tracking.geofence.edit`. **Responses**: `200`, `400`, `401`, `403`, `404`, `409`,
`500`.

## `DELETE /api/v1/tracking/geofences/{id}`

**D219 — soft delete.** `RBAC_MATRIX.md` não tinha `tracking.geofence.delete` antes desta
preparação — adicionado (D293), a única lacuna de código único (não de seção inteira) encontrada
neste módulo, já que `.view`/`.create`/`.edit` de Geofence já existiam.

**Segurança**: `tracking.geofence.delete`.

**Responses**: `204`, `401`, `403`, `404`, `422` — `TRACKING_GEOFENCE_IN_USE` (referenciada por
`configuracao_limite_velocidade_id`... na verdade por `eventos_rastreamento.cerca_eletronica_id`
histórico — excluir não apaga o histórico, D001, mas pode exigir confirmação explícita se houver
eventos recentes, detalhe de implementação), `500`.

## `SpeedLimitConfig` — Configuração de Limite de Velocidade

Cadastro relacionado, mesmo lote por ser pequeno e sem arquivo próprio pedido — `configuracoes_
limite_velocidade`.

### `GET /api/v1/tracking/speed-limit-configs`

**Segurança**: `tracking.speed_limit_config.view`. **Query parameters**: `page`/`limit`,
`vehicle_category_id`, `status`.

**Responses**: `200` (`Pagination` de `SpeedLimitConfig`), `401`, `403`, `500`.

### `GET /api/v1/tracking/speed-limit-configs/{id}`

**Achado do Backend Freeze**: implementado desde o Lote 8/9 (mesmo padrão de todo recurso com
listagem — `PATCH` já exige buscar o estado atual por `id`), mas nunca declarado neste contrato —
lacuna de documentação, nunca *scope creep* (nenhuma regra nova, só o `GET` unitário padrão que
toda listagem já tem em outro lugar desta API). Adicionado aqui para o contrato refletir a
implementação real.

**Segurança**: `tracking.speed_limit_config.view`.

**Responses**: `200` (`SpeedLimitConfig`), `401`, `403`, `404`, `500`.

### `POST /api/v1/tracking/speed-limit-configs`

`RBAC_MATRIX.md` só tinha `.view`/`.edit` para `speed_limit_config` antes desta preparação —
impossível cadastrar uma nova configuração via API, só editar as existentes. Corrigido: `tracking.
speed_limit_config.create` adicionado (D293, mesma auditoria).

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          vehicle_category_id: { $ref: "components/schemas.md#/UUID" }
          limit_kmh: { type: string }
        required: [limit_kmh]
```

`vehicle_category_id` ausente = configuração padrão do tenant (aplica-se a categorias sem
configuração própria).

**Segurança**: `tracking.speed_limit_config.create`.

**Responses**: `201` (`SpeedLimitConfig`), `400`, `401`, `403`, `404` (Categoria não existe), `500`.

### `PATCH /api/v1/tracking/speed-limit-configs/{id}`

D229 — parcial (`limit_kmh`, `status`).

**Segurança**: `tracking.speed_limit_config.edit`. **Responses**: `200`, `400`, `401`, `403`,
`404`, `500`.

### Sem `DELETE`

`RBAC_MATRIX.md` não tem `.delete` para `speed_limit_config` — desativação via `PATCH
status=INATIVA`, mesmo padrão de `046-tracking-providers.md`.

## Como este documento cresce

Se `SpeedLimitConfig` crescer em uso, pode migrar para um arquivo próprio (`054-speed-limit-
configs.md`) — hoje cabe aqui por ser pequeno e tematicamente próximo (ambos alimentam
`051-tracking-events.md`'s `ENTROU_GEOFENCE`/`EXCESSO_DE_VELOCIDADE`).
