# 051 — Tracking Events (Eventos de Rastreamento)

Bounded context proprietário: `tracking` (D215). `eventos_rastreamento` — derivado (D119), **nunca
substitui a leitura bruta**: Posição/Telemetria continuam consultáveis mesmo depois de um Evento
gerado a partir delas.

## D288 — eventos derivados referenciam a origem

`TrackingEvent.position_id`/`.geofence_id`/`.speed_limit_config_id` são sempre referências (D288) —
nenhum dado da Posição/Geofence/Configuração original é copiado para o Evento; o cliente busca o
detalhe via `048-vehicle-positions.md`/`052-geofences.md` quando precisar.

## D294 — uma tabela física, múltiplas permissões por categoria

`eventos_rastreamento` é uma única tabela com `tipo` discriminando 7 categorias, mas
`RBAC_MATRIX.md` §7.16 já fragmentava a autorização por categoria **antes** deste lote
(`tracking.stop.view`/`.route_deviation.view`/`.speed_event.view` — três códigos para um subconjunto
dos 7 valores de `tipo`). Não havia código para `ENTROU_GEOFENCE`/`SAIU_GEOFENCE`/
`IGNICAO_LIGADA`/`IGNICAO_DESLIGADA`.

| `tipo` | Permissão exigida |
|---|---|
| `PARADA_DETECTADA` | `tracking.stop.view` |
| `DESVIO_DE_ROTA_DETECTADO` | `tracking.route_deviation.view` |
| `EXCESSO_DE_VELOCIDADE` | `tracking.speed_event.view` |
| `ENTROU_GEOFENCE` / `SAIU_GEOFENCE` | `tracking.geofence.view` (reaproveitado — entrar/sair é extensão natural de ver a geofence) |
| `IGNICAO_LIGADA` / `IGNICAO_DESLIGADA` | `tracking.position.view` (reaproveitado — ignição é sinal básico de veículo, mais próximo de Posição que de qualquer categoria específica) |

Nenhum código novo foi criado para as duas categorias sem permissão própria — reaproveitamento
documentado (D294), mesmo princípio de D240/D260 aplicado pela primeira vez a **autorização por
subconjunto de linhas** de uma mesma tabela, não por campo (D267, Lote 7) nem por verbo (D240,
Lote 4).

## `GET /api/v1/tracking/events`

**Cursor pagination obrigatória** (D287) — `eventos_rastreamento` é "Alto" volume
(`HIGH_VOLUME_ENTITIES.md`), particionada mensalmente.

**Segurança**: `bearerAuth` + pelo menos uma das cinco permissões da tabela acima.

**Filtragem por linha (D294)**: quando o filtro `type` é omitido, a coleção retorna só as
categorias para as quais o chamador tem a permissão correspondente — nunca um `403` genérico nem
todas as categorias sem checagem. Quando `type` é informado explicitamente para uma categoria sem
a permissão correspondente, a resposta é `403`.

**Query parameters**:

| Parâmetro | Mapeia para |
|---|---|
| `cursor`/`limit` | paginação |
| `type` | `tipo` |
| `severity` | `severidade` (`INFORMACAO`/`ATENCAO`/`ALERTA`/`CRITICO`) |
| `vehicle_id` | `veiculo_tracionador_id` |
| `occurred_at__gte`/`__lte` | `data_hora` |

**Sem filtro `equipment_id`** — `eventos_rastreamento` não tem coluna física
`equipamento_rastreamento_id` (D226, filtro só existe se o dado existe fisicamente); para chegar ao
equipamento, o cliente segue `position_id → 048 → equipment_id`.

**Responses**: `200` (coleção cursor-paginada de `TrackingEvent`, `tracking-schemas.md`), `401`,
`403`, `500`.

## `GET /api/v1/tracking/events/{id}`

**Segurança**: mesma checagem por categoria da tabela acima, aplicada ao `type` do registro
específico.

**Responses**: `200` (`TrackingEvent`), `401`, `403`, `404`, `500`.

## Sem `POST`/`PATCH`/`DELETE`

D286 aplicado a eventos derivados também — nascem do processamento interno de Posição/Telemetria
contra Geofence/Configuração de Velocidade, nunca de um comando de usuário.

## Como este documento cresce

Se um oitavo `tipo` for adicionado ao Enum físico (`eventos_rastreamento_tipo_enum`), a tabela de
mapeamento acima ganha uma linha nova — reaproveitando o código mais próximo existente ou, se
`RBAC_MATRIX.md` ganhar um código dedicado, atualizando a referência, nunca inventando um código
novo diretamente aqui.
