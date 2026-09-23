# 018 — Trip Status: Comandos e Transições

Documento formal dos comandos de domínio da Viagem — bounded context `freight` (D215). Referência
canônica da máquina de estados é sempre [`../flows/002-VIAGEM.md`](../flows/002-VIAGEM.md); este
documento nunca a redefine, só mapeia cada transição já existente para um comando HTTP (ou explica
por que não existe comando para ela). **Nenhum estado novo foi inventado aqui** — toda linha abaixo
foi conferida contra `002-VIAGEM.md` e `RBAC_MATRIX.md` 7.12 nesta preparação (D200 aplicado à
API).

## D233/D234 — como ler este documento

Status não muda por `PATCH` (D233). Todo comando é orientado a intenção, nunca um `set_status`
genérico (D234): `POST /viagens/{id}/commands/<verbo>`. D235 — quando o comando é sintaticamente
válido mas a transição não é permitida no estado atual, a resposta é sempre `409 Conflict` com
`error.code` de domínio (nunca `422` para isso especificamente — `422` fica reservado para
violação de regra de negócio que não é sobre o estado da máquina, ex.: campo obrigatório
condicional). D238 — toda resposta de comando bem-sucedido devolve o `Trip` inteiro atualizado
(nunca só `204`), para o Frontend nunca precisar adivinhar o resultado.

## Três dimensões — só uma tem comandos neste contrato

| Dimensão | Comandos nesta API? | Como muda de verdade |
|---|---|---|
| **Operacional** | Sim — ver tabela completa abaixo | Comandos `freight` |
| **Fiscal** | **Não** | Consequência de eventos de `documents` (emissão/encerramento de CT-e/MDF-e, `007-fiscal.md`/lote de API fiscal futuro) — `viagens.status_fiscal` é sempre `readOnly` neste contrato |
| **Financeiro** | **Não** | Consequência de eventos de `financial` (faturamento/recebimento) — `viagens.status_financeiro` é sempre `readOnly` |
| **Composto (`ENCERRADA`)** | **Nunca, para ninguém** | Derivado automaticamente quando as três convergem (D019/D020) — nem Administrador SaaS tem um comando para isso; `Trip.status.closed` é `readOnly` sempre (`trip-schemas.md`) |

## Tabela completa de transições (Status Operacional)

| De | Para | Tipo | Comando/gatilho |
|---|---|---|---|
| `RASCUNHO` | `PLANEJADA` | **Derivada** | Automática ao completar a primeira alocação de recursos (`016-trip-resources.md`, `POST /resources`) — sem comando próprio |
| `PLANEJADA` | `AGUARDANDO_CHECKLIST` | **Derivada** | Automática, quando a Viagem está pronta para a data/rota programada — sem comando próprio, sem RBAC dedicado |
| `AGUARDANDO_CHECKLIST` | `LIBERADA` | **Externa, fora de escopo** | Depende do fluxo de Checklist (`maintenance`, [`../flows/007-CHECKLIST.md`](../flows/007-CHECKLIST.md)) — **documento ainda não escrito**; sem endpoint de Checklist, esta transição não é alcançável via API neste lote |
| `LIBERADA` | `EM_DESLOCAMENTO` | **Comando** | `commands/dispatch` (web, Gestor) **ou** `commands/start` (app, Motorista) — mesma transição, dois pontos de entrada |
| `EM_DESLOCAMENTO` | `CARREGANDO` | **Externa, fora de escopo** | Depende de `POST` em Coleta (`coletas`, sem endpoint neste lote — `015-trip-deliveries.md`, seção "Fora de escopo") |
| `CARREGANDO` | `EM_TRANSITO` | **Externa, fora de escopo** | Depende de Romaneio conferido (`romaneios`/`itens_carga`, sem endpoint neste lote) |
| `EM_TRANSITO` | `EM_ENTREGA` | **Derivada** | Automática ao iniciar o atendimento da próxima Entrega `PENDENTE` (`015-trip-deliveries.md`) |
| `EM_ENTREGA` | `EM_TRANSITO` | **Derivada** | Automática quando a Entrega da parada atual atinge estado terminal e ainda há Entregas `PENDENTE` (multi-drop) |
| `EM_ENTREGA` | `FINALIZADA` | **Comando** | `commands/finish` — só quando a última Entrega atinge estado terminal (pré-condição verificada pelo comando, não automática) |
| `EM_DESLOCAMENTO`/`CARREGANDO`/`EM_TRANSITO`/`EM_ENTREGA` | `INTERROMPIDA` | **Comando** | `commands/interromper` |
| `INTERROMPIDA` | *(estado de origem)* | **Comando** | `commands/retomar` |
| `INTERROMPIDA` | `CANCELADA` | **Comando** | `commands/cancelar` |
| `RASCUNHO`/`PLANEJADA`/`AGUARDANDO_CHECKLIST`/`LIBERADA` | `CANCELADA` | **Comando** | `commands/cancelar` |
| `PLANEJADA` | `PLANEJADA` *(sem mudança de estado)* | **Comando, aditivo** | `commands/accept` — `MotoristaAceitouViagem` (D129), nunca uma transição real |
| *(qualquer estado ativo)* | *(mesmo estado)* | **Comando, exceção administrativa** | `commands/close-administrative` — não é a transição normal para `FINALIZADA`, é o "encerramento administrativo forçado" documentado em `002-VIAGEM.md` (Gestor Operacional/Administrador SaaS, com justificativa obrigatória) |

## Comandos — detalhamento

### `POST /viagens/{id}/commands/accept`

| Campo | Valor |
|---|---|
| Estado atual permitido | `PLANEJADA` |
| Ação | Motorista aceita a Viagem já atribuída a ele |
| Novo estado | `PLANEJADA` *(sem mudança — D129)* |
| Permissão RBAC | `freight.trip.edit` (D240 — sem código dedicado, lacuna registrada, não inventada) |
| Pré-condições | Ator autenticado é o `driver_id` da alocação vigente |
| Evento publicado | `MotoristaAceitouViagem` (D129/D239 — adicionado a `EVENT_MAP.md` nesta preparação) |
| Consumidores | `mobile`, `notification_center`, `audit` |
| Erros possíveis | `401`, `403`, `404`, `409` — `FREIGHT_TRIP_ALREADY_ACCEPTED` (idempotência de negócio: aceitar duas vezes não é erro grave, mas a API informa que já foi aceito) |

### `POST /viagens/{id}/commands/dispatch`

| Campo | Valor |
|---|---|
| Estado atual permitido | `LIBERADA` |
| Ação | Gestor Operacional confirma o despacho |
| Novo estado | `EM_DESLOCAMENTO` |
| Permissão RBAC | `freight.trip.dispatch` |
| Pré-condições | Checklist aprovado (já implícito em ter alcançado `LIBERADA`) |
| Corpo (opcional) | `{"departure_odometer_km": "123456.00"}` — **Reconciliado (V1 Operational Hardening, Parte 2)**: grava a leitura de fronteira de despacho em `leituras_hodometro` (`fleet`, D034) via `TripOdometerRecorder`; omitido, a Viagem simplesmente fica sem `km_rodado` depois — nunca estimado |
| Evento publicado | `ViagemDespachada` |
| Consumidores | `documents` (emissão de CT-e), `tracking`, `mobile`, `notification_center`, `fleet` (leitura de hodômetro) |
| Erros possíveis | `401`, `403`, `404`, `409` — `FREIGHT_TRIP_INVALID_TRANSITION`; `422` — `FLEET_ODOMETER_READING_LOWER_THAN_LAST` (hodômetro informado menor que a última leitura do Veículo — a transição da Viagem já havia comitado, mesmo trade-off já aceito para CT-e/Disponibilidade neste comando) |

### `POST /viagens/{id}/commands/start`

| Campo | Valor |
|---|---|
| Estado atual permitido | `LIBERADA` |
| Ação | Motorista inicia o deslocamento (app) |
| Novo estado | `EM_DESLOCAMENTO` |
| Permissão RBAC | `freight.trip.start` (Escopo Próprio usuário — só o Motorista da alocação vigente) |
| Pré-condições | Ator é o `driver_id` vigente |
| Corpo (opcional) | `{"departure_odometer_km": "123456.00"}` — mesmo campo/efeito de `dispatch` (V1 Operational Hardening, Parte 2); o app do Motorista, fisicamente no veículo, é o ponto mais natural para informá-lo |
| Evento publicado | `ViagemDespachada` *(mesmo evento de `dispatch` — mesma transição, origem diferente registrada em `viagem_status_history.origem = 'app_motorista'`)* |
| Consumidores | Idem `dispatch` |
| Erros possíveis | `401`, `403` (ator não é o Motorista alocado), `404`, `409` |

### `POST /viagens/{id}/commands/finish`

| Campo | Valor |
|---|---|
| Estado atual permitido | `EM_ENTREGA` |
| Ação | Encerra o ciclo operacional da Viagem |
| Novo estado | `FINALIZADA` |
| Permissão RBAC | `freight.trip.finish` |
| Pré-condições | Todas as Entregas em estado terminal; todos os Canhotos correspondentes registrados |
| Corpo (opcional) | `{"arrival_odometer_km": "123706.50"}` — **Reconciliado (V1 Operational Hardening, Parte 2)**: grava a leitura de fronteira de encerramento; quando a Viagem também tem a leitura de despacho, `Trip.km_rodado` é calculado e gravado (`leitura_encerramento − leitura_despacho`) — nunca estimado quando faltar uma das duas |
| Evento publicado | `ViagemConcluida` |
| Consumidores | `financial`, `analytics`, `audit`, `fleet` (leitura de hodômetro) |
| Erros possíveis | `401`, `403`, `404`, `409` (estado errado), `422` — `FREIGHT_TRIP_DELIVERIES_PENDING` (pré-condição de Entregas/Canhotos não satisfeita — erro de regra de negócio, não de máquina de estados, por isso `422` e não `409`, D235); `422` — `FLEET_ODOMETER_READING_LOWER_THAN_LAST` (hodômetro de chegada menor que a última leitura do Veículo — a transição da Viagem já havia comitado, `km_rodado` fica indisponível, nunca negativo) |

**`Idempotency-Key` obrigatória** (seção 15 do pedido).

### `POST /viagens/{id}/commands/interromper`

| Campo | Valor |
|---|---|
| Estado atual permitido | `EM_DESLOCAMENTO`, `CARREGANDO`, `EM_TRANSITO`, `EM_ENTREGA` |
| Ação | Pane, sinistro ou ocorrência grave interrompe a execução |
| Novo estado | `INTERROMPIDA` (o estado de origem é guardado para a retomada) |
| Permissão RBAC | `freight.trip.edit` (D240 — lacuna registrada) |
| Pré-condições | `notes` (observação) obrigatória — `viagem_status_history.observacao` é obrigatória nesta transição (D007) |
| Evento publicado | `ViagemInterrompida` |
| Consumidores | `maintenance` (se originada de pane), `notification_center`, `support`, `audit` |
| Erros possíveis | `400` (`notes` ausente), `401`, `403`, `404`, `409` |

**`Idempotency-Key` obrigatória** (seção 15 do pedido — "interromper" está implícito em "eventos
críticos").

### `POST /viagens/{id}/commands/retomar`

| Campo | Valor |
|---|---|
| Estado atual permitido | `INTERROMPIDA` |
| Ação | Ocorrência resolvida, a Viagem retoma |
| Novo estado | O estado de onde a Viagem foi interrompida (guardado internamente, nunca informado pelo cliente) |
| Permissão RBAC | `freight.trip.edit` (D240) |
| Pré-condições | Nenhuma adicional |
| Evento publicado | Não catalogado explicitamente em `EVENT_MAP.md`/`002-VIAGEM.md` como evento próprio — a retomada é modelada como a *ausência* de uma nova Ocorrência crítica, tratada como reversão de `ViagemInterrompida`; documentado aqui como lacuna de nomenclatura de evento, não inventado um nome novo |
| Consumidores | — |
| Erros possíveis | `401`, `403`, `404`, `409` |

### `POST /viagens/{id}/commands/cancelar`

| Campo | Valor |
|---|---|
| Estado atual permitido | `RASCUNHO`, `PLANEJADA`, `AGUARDANDO_CHECKLIST`, `LIBERADA`, `INTERROMPIDA` |
| Ação | Cancelamento antes do início, ou perda definitiva após interrupção |
| Novo estado | `CANCELADA` |
| Permissão RBAC | `freight.trip.cancel` |
| Pré-condições | `notes` obrigatória (transição de exceção, D007); confirmação explícita (D010) — `Idempotency-Key` cobre o reenvio, mas a UI ainda precisa de uma confirmação própria antes de chamar o endpoint |
| Evento publicado | `ViagemCancelada` |
| Consumidores | `financial` (estorna cobrança pendente), `notification_center`, `audit` |
| Erros possíveis | `400`, `401`, `403`, `404`, `409` — inclui a regra normativa "não é permitido cancelar direto de `EM_TRANSITO`/`EM_ENTREGA`/`CARREGANDO`/`EM_DESLOCAMENTO`" (`002-VIAGEM.md`) |

**`Idempotency-Key` obrigatória** (seção 15 do pedido).

### `POST /viagens/{id}/commands/close-administrative`

| Campo | Valor |
|---|---|
| Estado atual permitido | Qualquer estado ativo anterior a `FINALIZADA`/`CANCELADA` |
| Ação | Encerramento administrativo forçado — **exceção documentada**, nunca a via normal de `FINALIZADA` |
| Novo estado | `FINALIZADA` (operacional) — **nunca** força `ENCERRADA` (D019, convergência continua exigindo Fiscal/Financeiro reais) |
| Permissão RBAC | `freight.trip.close` |
| Pré-condições | Justificativa obrigatória; ator é Gestor Operacional ou Administrador SaaS |
| Evento publicado | `ViagemConcluida` (mesmo evento de `finish`, com `origem` marcando o encerramento forçado na linha de `viagem_status_history`) |
| Consumidores | Idem `finish` |
| Erros possíveis | `400` (justificativa ausente), `401`, `403`, `404`, `409` |

## Reallocate — ver `016-trip-resources.md`

`commands/reallocate-resources` não muda o Status Operacional (D188) — documentado por completo
no arquivo de recursos, não repetido aqui.

## D236 — eventos nunca são publicados diretamente

Nenhum endpoint aceita `{"event": "ViagemConcluida"}` ou equivalente — todo evento nasce como
consequência de um comando processado com sucesso pelo Domain, nunca uma ação direta do cliente da
API. Não existe `POST /events`.

## Como este documento cresce

`commands/retomar`'s evento sem nome próprio e as duas transições "Externa, fora de escopo"
(Coleta/Romaneio) são as três lacunas mais visíveis deste lote — resolvidas quando os lotes
correspondentes (Coleta/Romaneio, e um nome de evento formal para retomada) forem escritos, sempre
Domain/EVENT_MAP primeiro (D101), API depois.
