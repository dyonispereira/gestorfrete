# AVAILABILITY_IMPLEMENTATION.md — `Disponibilidade do Veículo` (Read Model)

Contrato: [`../../api/025-vehicle-availability.md`](../../api/025-vehicle-availability.md). DDL:
[`../../database/relational/004-frota.md`](../../database/relational/004-frota.md)
(`disponibilidade_veiculo`). RBAC: `fleet.vehicle.view_availability` — **só essa**, nenhum
`.edit`/`.create` (D247).

## Por que este lote não consegue ligar o consumidor de eventos de verdade

`disponibilidade_veiculo` é populada por `ViagemDespachada`/`ViagemConcluida`/
`ViagemInterrompida` (`freight`) e `OrdemServicoAberta`/`OrdemServicoConcluida` (`maintenance`) —
nenhum dos dois bounded contexts existia ainda no backend na fundação deste read model (Lote 5+/
Lote 6+). Não há classes `DomainEvent` Python para esses eventos, então não há nada real para
assinar no `EventBus` ainda.

Resolvido implementando a **projeção em si** (tabela + Repository de leitura + um serviço de
aplicação que sabe como aplicar cada tipo de sinal) desde já, pronta para ser conectada a um
consumidor real assim que `freight`/`maintenance` existirem — só a fiação final (`EventBus.
subscribe(...)`) fica para quando esses eventos forem publicados de verdade. Os testes deste lote
chamam o serviço de aplicação diretamente com os parâmetros que um evento real carregaria —
exatamente o que um consumidor futuro faria ao receber a mensagem.

**Atualização — Lote Frota e Manutenção, Parte 2**: o lado `maintenance` está conectado de verdade
agora — `create_ordem_servico`/`concluir_ordem_servico`/`cancelar_ordem_servico` (e a abertura
automática de OS corretiva em `reject_checklist`) chamam `apply_service_order_opened`/
`apply_service_order_closed` diretamente após o commit da própria transação (mesmo padrão
cross-module síncrono de D390/D398 — não é o `EventBus` ainda, é uma chamada direta
Application→Application, já que nenhum `DomainEvent` real existe). O lado `freight`
(`apply_trip_dispatched`/`apply_trip_ended`) segue sem consumidor real — gap documentado, não
escondido, fora do escopo desta Lote.

## Domain/Application

```
modules/fleet/domain/
├── value_objects/availability_status.py     # DISPONIVEL / EM_VIAGEM / EM_MANUTENCAO / INATIVO
└── repositories/vehicle_availability_repository.py   # get_by_vehicle_id, list_page, apply(...)

modules/fleet/application/
└── availability_projector.py    # VehicleAvailabilityProjector — NÃO um CommandHandler
```

`VehicleAvailabilityProjector` expõe `apply_trip_dispatched(vehicle_id, driver_id, implement_id,
at)`, `apply_trip_ended(vehicle_id, at)`, `apply_service_order_opened(vehicle_id, at)`,
`apply_service_order_closed(vehicle_id, at)` — cada um faz um upsert direto em
`disponibilidade_veiculo` via `VehicleAvailabilityRepository.apply(...)`. Nenhum desses métodos é
acionável por HTTP — não existe router, não existe schema de request, não existe `Command`. É
literalmente a única forma de escrever nesta tabela em todo o código.

Um Veículo recém-criado **não** ganha uma linha em `disponibilidade_veiculo` automaticamente —
`CreateVehicleHandler` nunca toca nesta tabela (D247: só o projetor escreve). `GET
/veiculos/{id}/disponibilidade` retorna `404 FLEET_VEHICLE_AVAILABILITY_NOT_FOUND` até o primeiro
sinal ser aplicado — comportamento explícito do contrato (`025-vehicle-availability.md`: "cenário
raro, Veículo recém-criado antes do primeiro evento consumido"), não um bug.

## Interfaces

`interfaces/api/vehicle_availability_router.py` — **só** `GET /veiculos/disponibilidade`,
`GET /veiculos/{id}/disponibilidade`. Nenhum `POST`/`PATCH`/`DELETE` em nenhum arquivo deste router
— confirmado por grep, não assumido.

## Auditoria explícita pedida pelo usuário: prova de que não há caminho de escrita

Três verificações independentes, todas no mesmo teste de integração:

1. **Grep estrutural**: nenhum método `@router.post`/`@router.patch`/`@router.delete` existe em
   `vehicle_availability_router.py` (verificado lendo o arquivo, reforçado por teste que bate em
   `POST /veiculos/disponibilidade` e `PATCH /veiculos/{id}/disponibilidade` esperando `405 Method
   Not Allowed` — a rota nunca foi registrada).
2. **RBAC**: `fleet.vehicle.view_availability` é a única permissão referenciada em todo o módulo
   para este recurso — nenhuma `.edit`/`.create` existe em `RBAC_MATRIX.md` para checar contra.
3. **Repository**: `VehicleAvailabilityRepository` não herda `shared_kernel.domain.repository.
   Repository[...]` (que teria `add()` genérico) — é uma interface própria, menor, com só
   `get_by_vehicle_id`/`list_page`/`apply(...)`, e `apply(...)` só é chamado pelo
   `VehicleAvailabilityProjector`, nunca por um Command/Router.

## Erros

| Código | HTTP | Quando |
|---|---|---|
| `FLEET_VEHICLE_AVAILABILITY_NOT_FOUND` | 404 | Veículo existe, mas nenhum sinal foi aplicado ainda |

## Testes (D352 + auditoria dedicada)

- Unit: `VehicleAvailabilityProjector` aplicando cada tipo de sinal isoladamente.
- Integration: `VehicleAvailabilityRepository` contra Postgres real — tenant isolation.
- E2E: `GET /veiculos/{id}/disponibilidade` antes de qualquer sinal → `404`; chama o projetor
  diretamente (simulando o evento) → `GET` → `200` com o status esperado; `POST`/`PATCH` na rota →
  `405`.
