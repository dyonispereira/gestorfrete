# 016 — Trip Resources

Bounded context proprietário: `freight` (D215). Implementação HTTP de D188 — `alocacoes_recurso_
viagem` é um **pacote atômico** (Motorista + Veículo Tracionador + Implemento em uma linha), nunca
recursos independentes.

## Nunca isto

```
POST /viagem/{id}/motorista        -- não existe
POST /viagem/{id}/veiculo           -- não existe
POST /viagem/{id}/implemento         -- não existe
```

D188 é explícito: o invariante de domínio é "exatamente uma Alocação Vigente **por Viagem**"
(singular, atômica) — três endpoints por recurso quebrariam essa atomicidade (motorista e veículo
poderiam divergir de vigência sem uma reatribuição conjunta real). O contrato trabalha com a
estrutura já existente, um pacote só.

## `GET /api/v1/viagens/{id}/resources`

Retorna a alocação vigente (e, opcionalmente, o histórico de substituições).

**Segurança**: `bearerAuth` + `freight.trip.view`.

**Query parameters**: `?history=true` inclui alocações `SUBSTITUIDA`, não só a `VIGENTE` (default:
só a vigente).

**Responses**

| Código | Corpo |
|---|---|
| `200` | `TripAllocation` (vigente) ou `Pagination` de `TripAllocation` quando `?history=true` |
| `401` | `Unauthorized` |
| `403` | `Forbidden` |
| `404` | `NotFound` — Viagem não existe, ou nenhuma alocação ainda (Viagem em `RASCUNHO` sem recursos atribuídos) |
| `500` | `InternalServerError` |

## `POST /api/v1/viagens/{id}/resources`

Cria a **primeira** alocação de uma Viagem (nunca existiu uma `VIGENTE` antes) — dispara a
transição `RASCUNHO → PLANEJADA` quando todas as pré-condições da máquina de estados forem
atendidas (`018-trip-status.md`; a transição em si é derivada, não um comando separado).

**Segurança**: `freight.trip.edit` — a alocação inicial é tratada como parte da edição/montagem da
Viagem ainda em `RASCUNHO`, não uma "reatribuição" (`.reassign` é especificamente para *trocar* uma
alocação já vigente, ver comando abaixo).

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          driver_id: { $ref: "components/schemas.md#/UUID" }
          tractor_unit_id: { $ref: "components/schemas.md#/UUID" }
          implement_id: { $ref: "components/schemas.md#/UUID" }
        required: [driver_id, tractor_unit_id]
```

**Responses**: `201` (`TripAllocation`), `400`, `401`, `403`, `404`, `409` — `FREIGHT_TRIP_
ALREADY_HAS_ALLOCATION` (já existe uma `VIGENTE`; use o comando de realocação abaixo, nunca um
segundo `POST`), `422` — `FREIGHT_DRIVER_NOT_FIT`/`FREIGHT_VEHICLE_UNAVAILABLE` (Motorista com
`fitness_status = BLOQUEADO`, ou Veículo já alocado em outra Viagem vigente — regra de Aplicação,
não constraint física direta), `500`.

## `POST /api/v1/viagens/{id}/commands/reallocate-resources`

Comando explícito (D234) para **trocar** a alocação vigente — "Troca de cavalo mecânico"/"Troca de
motorista" em [`../flows/002-VIAGEM.md`](../flows/002-VIAGEM.md), permitido em qualquer estado de
`PLANEJADA` até `EM_ENTREGA`, sem alterar o Status Operacional da Viagem. **`Idempotency-Key`
obrigatória** (seção 15 do pedido — "reatribuir recursos" está na lista explícita).

**Nunca edita a linha histórica anterior** — a alocação `VIGENTE` atual vira `SUBSTITUIDA`
(imutável a partir daí) e uma nova linha `VIGENTE` é inserida, mesmo padrão de toda tabela
`*_status_history`/D017/D018 aplicado aqui via `status` em vez de uma tabela de histórico própria
(D188 já documentava isso: "motivo_troca" existe na própria linha nova, não na antiga).

**Segurança**: `freight.trip.reassign`.

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          driver_id: { $ref: "components/schemas.md#/UUID" }
          tractor_unit_id: { $ref: "components/schemas.md#/UUID" }
          implement_id: { $ref: "components/schemas.md#/UUID" }
          reason:
            type: string
            description: "`motivo_troca` — obrigatório neste comando (opcional na base física
              porque a primeira alocação nunca tem motivo de troca; a API exige aqui porque toda
              reatribuição, por definição, tem uma causa a auditar)."
        required: [driver_id, tractor_unit_id, reason]
```

**Efeito colateral documentado (D238 — resposta reflete o estado resultante)**: dispara
`ViagemReatribuida` (`EVENT_MAP.md`) — consumido por `financial`, `tracking`, `mobile`,
`notification_center`, `audit`. A resposta já traz a nova `TripAllocation` `VIGENTE`, o Frontend
nunca precisa de uma segunda chamada para saber o resultado.

**Responses**: `200` (`TripAllocation`, a nova vigente), `400`, `401`, `403`, `404`, `409`
(Idempotency-Key), `422` — mesmos códigos de disponibilidade de `POST`, mais
`FREIGHT_TRIP_NOT_ALLOCATABLE` (Viagem fora da janela `PLANEJADA`–`EM_ENTREGA`, ex.: já
`FINALIZADA`/`CANCELADA`), `500`.

## Composição Veicular — nota de escopo

Múltiplos implementos simultâneos (bitrem/rodotrem) **não** são resolvidos aqui — D188 já
estabeleceu que isso é responsabilidade de `Composição Veicular` (nível de frota, N:N com
Implemento, `004-frota.md`), não de `alocacoes_recurso_viagem` (que referencia no máximo um
`implement_id`, o implemento "principal" da composição usada nesta Viagem). Endpoint de
Composição Veicular fica para o lote de Frota, fora deste.

## Como este documento cresce

Nenhuma mudança prevista — o pacote atômico é uma decisão já validada (D188) e reforçada aqui;
qualquer proposta de "recurso independente" passa pela mesma avaliação que D188 já fez, nunca
aceita sem revisão explícita.
