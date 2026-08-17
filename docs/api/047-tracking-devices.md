# 047 — Tracking Devices (Equipamentos de Rastreamento)

Bounded context proprietário: `tracking` (D215). `equipamentos_rastreamento` — D128: um Veículo pode
ter múltiplos Equipamentos simultâneos, cada um com um papel (`PRINCIPAL`/`BACKUP`/`CAMERA`/
`SENSOR_TEMPERATURA`/`TPMS`/`OUTRO`); no máximo um `PRINCIPAL` vigente por vez, os demais papéis
coexistem livremente.

## D293 — RBAC não existia, corrigido na origem

Mesma auditoria de `046-tracking-providers.md`: `RBAC_MATRIX.md` §7.16 não tinha nenhum código para
Equipamento de Rastreamento. Corrigido: `tracking.equipment.view`/`.create`/`.edit` adicionados
antes de escrever este documento (D293).

## `GET /api/v1/tracking/equipment`

**Segurança**: `bearerAuth` + `tracking.equipment.view`.

**Query parameters**: `page`/`limit`, `vehicle_id` (`veiculo_tracionador_id`), `provider_id`
(`provedor_rastreamento_id`), `equipment_type` (`tipo_equipamento`), `status`.

**Responses**: `200` (`Pagination` de `TrackingEquipment`, `tracking-schemas.md`), `401`, `403`,
`500`.

## `GET /api/v1/tracking/equipment/{id}`

**Responses**: `200` (`TrackingEquipment`), `401`, `403`, `404`, `500`.

## `POST /api/v1/tracking/equipment`

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          provider_id: { $ref: "components/schemas.md#/UUID" }
          serial_identifier: { type: string }
          equipment_type: { type: string, enum: [PRINCIPAL, BACKUP, CAMERA, SENSOR_TEMPERATURA, TPMS, OUTRO] }
          vehicle_id: { $ref: "components/schemas.md#/UUID" }
        required: [provider_id, serial_identifier, equipment_type]
```

**D128 aplicado**: quando `equipment_type = PRINCIPAL` e `vehicle_id` já tem um `PRINCIPAL` vigente
(`data_fim_vigencia IS NULL`), a API **rejeita** a criação — `uq_equipamentos_rastreamento_
principal_vigente` (índice único parcial) não permite dois. Diferente de `023-vehicle-
compositions.md` (D248, que fecha a vigência anterior automaticamente), aqui o domínio não descreve
um comando de "troca atômica" — o cliente encerra a vigência do equipamento anterior explicitamente
(`PATCH .../{id}` com `ends_at`) antes de criar o novo `PRINCIPAL`. Escolha deliberada, mais
conservadora que D248, documentada aqui por não haver instrução equivalente no domínio para
Equipamento.

**Segurança**: `tracking.equipment.create`.

**Responses**: `201` (`TrackingEquipment`), `400`, `401`, `403`, `404` (Provedor/Veículo não
existe), `409` — `TRACKING_EQUIPMENT_PRINCIPAL_ALREADY_EXISTS` / `identificador_serial` duplicado,
`500`.

## `PATCH /api/v1/tracking/equipment/{id}`

D229 — parcial (`vehicle_id`, `ends_at`, `status`). Encerrar a vigência (`ends_at`) é o mecanismo
para liberar o papel `PRINCIPAL` de um veículo antes de atribuir um novo.

**Segurança**: `tracking.equipment.edit`. **Responses**: `200`, `400`, `401`, `403`, `404`, `409` —
`TRACKING_EQUIPMENT_PRINCIPAL_ALREADY_EXISTS` (se reatribuir `equipment_type = PRINCIPAL` para um
veículo que já tem um vigente), `500`.

## Sem `DELETE`

`RBAC_MATRIX.md` não tem `tracking.equipment.delete` — o Enum de `status` já inclui `REMOVIDO`
(distinto de `INATIVO`), cobrindo o caso de remoção física do equipamento sem apagar o registro
(D001) — `PATCH status=REMOVIDO`, nunca soft delete via `DELETE`.

## Como este documento cresce

Nenhuma mudança estrutural prevista — a vigência de Equipamento já cobre reatribuição/remoção sem
precisar de comando dedicado.
