# 023 — Vehicle Compositions

Bounded context proprietário: `fleet` (D215). A parte mais crítica deste lote — Composição
Veicular não é um cadastro simples: tem vigência, histórico, múltiplos Implementos, tipo de
combinação (D248/D249).

## D248 — nunca `PATCH` que edita a linha vigente

**Não existe `PATCH /vehicle-compositions/{id}`.** Trocar a composição de um Veículo Tracionador
(novo Implemento, mudança de `combination_type`) sempre fecha a vigência atual e cria uma nova
linha — mesmo padrão de `alocacoes_recurso_viagem` (Lote 4, D188) e de `TripAllocation`. A tabela
física (`composicoes_veiculares`) já reflete isso: `data_fim_vigencia` fecha a antiga,
`uq_composicoes_veiculares_vigente` (índice único parcial) garante só uma `VALIDA`+vigente por
Veículo Tracionador de cada vez. O histórico **é** a própria tabela (D037) — não existe endpoint
de "histórico de composição" separado, só o filtro `?vigente=false` na listagem.

## D249 — Composição pertence à Frota, não à Viagem

`alocacoes_recurso_viagem` (`016-trip-resources.md`) referencia o **resultado** de uma Composição
(via `implemento_id`, o implemento "principal"), nunca gerencia Composição diretamente — trocar de
bitrem para rodotrem é uma operação de Frota, disparada aqui, não em `/viagens/{id}/resources`.

## `GET /api/v1/vehicle-compositions`

**Segurança**: `bearerAuth` + `fleet.vehicle_composition.view`.

**Query parameters**: `page`/`limit`, `veiculo_tracionador_id`, `tipo_combinacao`
(`combination_type`), `vigente` (`true`/`false` — `data_fim_vigencia IS NULL`/`IS NOT NULL`;
default `true`, só a vigente de cada Veículo).

**Responses**: `200` (`Pagination` de `VehicleComposition`, `fleet-schemas.md`), `401`, `403`,
`500`.

## `GET /api/v1/vehicle-compositions/{id}`

**Segurança**: `fleet.vehicle_composition.view`. **Responses**: `200`, `401`, `403`, `404`, `500`.

## `POST /api/v1/vehicle-compositions`

Cria uma nova composição — se já existir uma vigente para o mesmo `tractor_unit_id`, esta chamada
**fecha a anterior automaticamente** (D248) antes de inserir a nova, numa única transação. Nunca
duas chamadas separadas (uma para fechar, outra para abrir) — o cliente da API nunca manipula
`ends_at` diretamente.

**Segurança**: `fleet.vehicle_composition.create`.

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          tractor_unit_id: { $ref: "components/schemas.md#/UUID" }
          combination_type: { type: string, enum: [SIMPLES, BITREM, RODOTREM] }
          total_axles: { type: integer }
          implements:
            type: array
            items:
              type: object
              properties:
                implement_id: { $ref: "components/schemas.md#/UUID" }
                order: { type: integer, minimum: 1 }
              required: [implement_id, order]
        required: [tractor_unit_id, combination_type, total_axles, implements]
```

**Responses**: `201` (`VehicleComposition`), `400`, `401`, `403`, `404` (Veículo/Implemento não
existe), `422` — `FLEET_COMPOSITION_AXLES_MISMATCH` (regra de negócio: eixos totais incompatíveis
com o tipo de combinação — validação de aplicação, não constraint física), `500`.

## `POST /api/v1/vehicle-compositions/{id}/commands/validate`

Comando explícito para `fleet.vehicle_composition.validate` ("Validar composição veicular
(CONTRAN)", `RBAC_MATRIX.md`) — marca `status: VALIDA`/`INVALIDA` conforme conformidade
regulatória (regra de negócio de validação de combinação veicular, não fixada em detalhe aqui,
fora do escopo deste lote definir o algoritmo exato).

**Segurança**: `fleet.vehicle_composition.validate`.

**Responses**: `200` (`VehicleComposition` atualizada), `401`, `403`, `404`, `500`.

## Sem `DELETE`

`RBAC_MATRIX.md` não tem `fleet.vehicle_composition.delete`. Encerrar uma composição sem abrir uma
nova é feito criando uma composição `SIMPLES` sem Implementos (ou, mais simples ainda: deixando o
Veículo Tracionador sem composição vigente não é uma operação modelada — todo Veículo Tracionador
em uso normalmente tem uma composição `SIMPLES` de baseline). Não decidido em detalhe neste lote —
lacuna documentada, não inventada.

## Como este documento cresce

Regra exata de validação CONTRAN (`commands/validate`) é candidata a expandir quando o algoritmo
de negócio for detalhado — endpoint já reservado, comportamento interno evolui sem quebrar o
contrato.
