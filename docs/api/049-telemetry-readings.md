# 049 — Telemetry Readings (Leituras de Telemetria)

Bounded context proprietário: `tracking` (D215). `leituras_telemetria` — Time Series (D191), EAV
(D120): uma linha por sensor por instante, nunca uma coluna por sensor.

## D293 — RBAC não existia, corrigido na origem

`RBAC_MATRIX.md` §7.16 não tinha nenhum código para Telemetria. Corrigido: `tracking.telemetry.
view` adicionado antes de escrever este documento.

## D286/D292 — somente leitura, três timestamps distintos

Mesmo padrão de `048-vehicle-positions.md`: dados brutos entram só via integração, nunca `POST`/
`PATCH`/`DELETE` nesta API. `captured_at`/`received_at`/`processed_at` nunca colapsam em um único
campo (D125/D292).

## `GET /api/v1/vehicles/{vehicleId}/tracking/telemetry`

**Cursor pagination obrigatória** (D287).

**Segurança**: `bearerAuth` + `tracking.telemetry.view`.

**Query parameters**:

| Parâmetro | Mapeia para |
|---|---|
| `cursor`/`limit` | paginação |
| `sensor_type` | `tipo_sensor` (`IGNICAO`/`VELOCIDADE`/`BATERIA`/`TENSAO`/`ODOMETRO`/`HORIMETRO`/`RPM`/`TEMPERATURA`/`COMBUSTIVEL`/`ACELERACAO`/`FRENAGEM`) |
| `captured_at__gte`/`__lte` | período |
| `equipment_id` | `equipamento_rastreamento_id` |

**Não criar endpoint por sensor** (pedido explícito) — `sensor_type` é sempre um filtro de query,
nunca um path segment (`/telemetry/rpm` não existe) — reforça D120 (vocabulário extensível sem
mudança estrutural).

**Responses**: `200` (coleção cursor-paginada de `TelemetryReading`, `tracking-schemas.md`), `401`,
`403`, `404` (Veículo não existe), `500`.

## D126 — ausência de sensor nunca é erro

A ausência de um `sensor_type` específico no período consultado não gera `404`/erro — é o estado
normal esperado (nem todo equipamento envia todos os sensores); a resposta é simplesmente uma
coleção vazia para aquele filtro.

## Como este documento cresce

Novo `sensor_type` (D120, "Requisitos futuros": pressão dos pneus, ABS, eixo levantado, porta
aberta, sensor de fadiga, câmera IA) entra via `ALTER TYPE` no Enum físico — o contrato aqui não
muda, o novo valor já é aceito pelo mesmo filtro `sensor_type`.
