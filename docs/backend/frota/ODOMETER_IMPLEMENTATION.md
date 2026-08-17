# ODOMETER_IMPLEMENTATION.md — `Leitura de Hodômetro`

Contrato: [`../../api/024-odometer-readings.md`](../../api/024-odometer-readings.md). DDL:
[`../../database/relational/004-frota.md`](../../database/relational/004-frota.md)
(`leituras_hodometro`). RBAC: `fleet.odometer_reading.*` (`RBAC_MATRIX.md` §7.8 — só `.view`/
`.create`).

Time Series/Histórica (D037/D050) — nunca `PATCH`/`DELETE` (D246), cursor pagination (não Offset).

## Domain

```
modules/fleet/domain/
├── value_objects/odometer_origin.py      # ABASTECIMENTO / CHECKLIST / MANUAL / TELEMETRIA
└── entities/odometer_reading.py          # OdometerReading(BaseEntity[UUID]) — não-Aggregate-Root
```

`OdometerReading.create(veiculo_tracionador_id, valor_km, origem, viagem_id, now)` — sem método
`update`: é imutável por design (D246), a única operação é `create`.

## Invariante "nunca decresce" (D365) — validação de Application, não trigger

`RegisterOdometerReadingHandler` busca a última leitura do veículo
(`OdometerReadingRepository.get_latest_for_vehicle`) **dentro da mesma transação/UoW** antes de
inserir, e rejeita com `422 FLEET_ODOMETER_READING_LOWER_THAN_LAST` se `valor_km` for menor.
Deliberadamente não um trigger `BEFORE INSERT` (a DDL autoriza os dois, D365) — seria o primeiro
trigger PL/pgSQL do projeto, introduzindo um padrão novo sem necessidade real neste volume.

## Infrastructure

`OdometerReadingModel` — tabela `leituras_hodometro`, `PARTITION BY RANGE (data_hora)` com uma
partição `DEFAULT` (D364, mesmo padrão de `logs_auditoria`, Lote 2) em vez da partição fixa
`leituras_hodometro_2026_01` literal da DDL, que ficaria inválida assim que o mês virasse.
`viagem_id` aceito, sem FK física (`viagens`/`freight` é Lote 5+, mesmo padrão de D355).

`SqlAlchemyOdometerReadingRepository.list_for_vehicle_cursor(...)` — cursor pagination real: cursor
opaco Base64 de `{data_hora, id}` da última linha da página anterior, reaproveitando o índice
`(veiculo_tracionador_id, data_hora DESC)` já catalogado na DDL (`PAGINATION.md`'s regra: cursor
sem reaproveitar o índice já existente não é aceito).

## Interfaces

`interfaces/api/odometer_reading_router.py` — `GET/POST /veiculos/{id}/odometro/leituras`. Envelope
de resposta do `GET`: `{"data": [...], "meta": {"pagination": {"next_cursor": ..., "has_more":
bool}}}` (`PAGINATION.md`), nunca `page`/`total` (Time Series nunca expõe contagem total).

## Erros

| Código | HTTP | Quando |
|---|---|---|
| `FLEET_ODOMETER_READING_LOWER_THAN_LAST` | 422 | `valor_km` menor que a última leitura do veículo |

## Testes (D352)

- Unit: `OdometerReading.create()`.
- Integration: Repository real — tenant isolation, cursor pagination (`next_cursor`/`has_more`
  corretos), `get_latest_for_vehicle`.
- E2E: `POST` leitura 100km → `POST` leitura 150km (aceita) → `POST` leitura 120km (rejeitada,
  `422`) → `GET` com cursor confirma ordem `data_hora DESC` e paginação real via HTTP.
- Auditoria: `POST` gera `logs_auditoria` (`entidade_tipo=leituras_hodometro`).
