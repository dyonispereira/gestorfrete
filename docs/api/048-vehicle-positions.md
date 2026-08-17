# 048 — Vehicle Positions (Posições)

Bounded context proprietário: `tracking` (D215). `posicoes_veiculo` — Time Series (D191), a entidade
mais consultada do sistema (`relational/008-rastreamento.md`).

## D285/D286 — somente observacional, somente leitura

A API de Tracking nunca altera status operacional de Viagem/Veículo (D285) — Posição é dado puro de
observação. **D286**: dados brutos de rastreamento entram só via integração/inbound pipeline, nunca
por comando de usuário nesta API pública. **Sem `POST`/`PATCH`/`DELETE` neste documento.**

## Tensão registrada, não escondida: `tracking.position.create_manual`

`RBAC_MATRIX.md` §7.16 tem `tracking.position.create_manual` ("Registrar posição manual", Gestor
Operacional), e `flows/008-RASTREAMENTO.md` descreve explicitamente a "Atualização manual em lote"
como um fluxo real (justificativa obrigatória, confiabilidade Baixa marcada `MANUAL`) — não uma
lacuna, uma funcionalidade genuína do domínio. **Ainda assim, por instrução explícita deste lote**
("Somente leitura. Nunca: POST/PATCH/DELETE"), nenhum endpoint de escrita é criado aqui. A
funcionalidade de entrada manual fica reservada para quando o contrato de ingestão (webhook/
polling/API do Provedor/queue) for definido — entrada manual é, na prática, um caso especial de
ingestão iniciado por humano em vez de automatizado, então cabe no mesmo lote futuro, não neste.

## `GET /api/v1/vehicles/{vehicleId}/tracking/positions`

**Cursor pagination obrigatória** (D287) — nunca offset, mesmo para períodos curtos (consistência
de contrato, independe do volume real de cada consulta).

**Segurança**: `bearerAuth` + `tracking.position.view`.

**Query parameters**:

| Parâmetro | Mapeia para |
|---|---|
| `cursor`/`limit` | paginação |
| `captured_at__gte`/`__lte` | `capturado_em` (período) |
| `origin` | `origem_localizacao_id` (nome resolvido) |
| `equipment_id` | `equipamento_rastreamento_id` |

**Responses**: `200` (coleção cursor-paginada de `VehiclePosition`, `tracking-schemas.md`), `401`,
`403`, `404` (Veículo não existe), `500`.

## `GET /api/v1/tracking/origins`

Platform Reference Data (D046) — `origens_localizacao`, sem `tenant_id`. Exposto aqui (não em
arquivo próprio) porque só existe para dar sentido ao filtro `?origin=` acima — mesmo raciocínio de
D260 (referência necessária para interpretar/filtrar o recurso pedido), aplicado a um filtro em vez
de a uma FK bloqueante de escrita.

**Segurança**: `tracking.position.view` — `RBAC_MATRIX.md` não tem código próprio para "ver
catálogo de origens"; reaproveitado por ser Platform Reference Data de baixa sensibilidade, mesmo
padrão de `/permissions` (Lote 2).

**Responses**: `200` (`Pagination` de `LocationOrigin`), `401`, `403`, `500`.

## Fora de escopo, não esquecido

- **Entrada manual de posição** (`tracking.position.create_manual`): RBAC e domínio existem, sem
  endpoint — ver "Tensão registrada" acima.
- **Contrato de ingestão** (webhook/polling/API do Provedor/queue): decisão de arquitetura ainda não
  tomada — nenhum `POST /tracking/positions` genérico é criado até essa decisão existir.

## Como este documento cresce

Quando o contrato de ingestão for definido, este documento pode ganhar uma seção linkando para o
lote/arquivo correspondente — a leitura aqui documentada permanece estável independente de como os
dados chegam.
