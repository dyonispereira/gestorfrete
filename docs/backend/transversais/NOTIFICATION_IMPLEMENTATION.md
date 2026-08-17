# NOTIFICATION_IMPLEMENTATION.md — Notificação/Preferência de Canal (086)

Bounded context `notification_center` (`apps/api/src/modules/notification_center/`). `Notificação`/
`Preferência de Canal` nasceram em Domain/DDL neste próprio lote (D323) — RBAC já as antecipava.

## D414 — conjunto mínimo de 2 eventos, nunca o catálogo inteiro

`NotificationDispatcher` (`application/notification_dispatcher.py`) — mesmo formato de tabela de
despacho em processo do `SYNC_COMMAND_HANDLERS` (D410): um dicionário `event_type → build_notification`
callable, chamado **sincronamente**, dentro da mesma transação do Handler que publica o evento de
origem (nunca via RabbitMQ — o Event Bus real publica de qualquer forma para consumidores futuros
fora deste contrato, mas a criação da linha `notificacoes` não pode depender de um worker existir).

- `DispatchTripHandler` (`ViagemDespachada`) chama `NotificationDispatcher.notify_trip_dispatched`
  depois do commit da transição — resolve o Usuário do Motorista alocado
  (`UserRepository.get_by_driver_id_and_tenant`, mesmo método já usado pelo login Mobile, D408) e
  cria uma Notificação `IN_APP`, título "Viagem despachada", a menos que
  `usuario_destinatario_id == actor.user_id` (motorista despachando a própria viagem via
  `commands/start` nunca notifica a si mesmo).
- `CreateOccurrenceHandler` (`OcorrenciaRegistrada`) chama `NotificationDispatcher.
  notify_occurrence_registered` depois do commit — destinatário é `trip.criado_por` (snapshot de
  auditoria já existente em `viagens.criado_por`, nenhuma coluna nova), mesmo guard de auto-
  notificação.

## `Preferência de Canal` consultada antes de criar, nunca depois

Antes de inserir `notificacoes`, o Dispatcher consulta `PreferenceRepository.get(usuario_id, canal)`
— ausência de linha em `preferencias_notificacao` significa `habilitado=true` (default do contrato,
"quando nenhuma preferência foi salva ainda"), nunca uma segunda leitura default hardcoded em dois
lugares. Canal desabilitado = a Notificação simplesmente não é criada (nenhuma linha "descartada"
registrada — mesma disciplina econômica de não inventar uma tabela de log que ninguém pediu).

## Endpoints — `GET /notifications`, `GET /{id}`, `POST /{id}/commands/mark-read`, `GET`/`PATCH channel-preferences`

Todos escopados ao `actor.user_id` da sessão — `GET /notifications/{id}` de outro usuário é `403`
(nunca `404`, mesmo padrão de enumeration-safety já usado em toda a API desde o Lote 4), mesmo para
Gestor com toda permissão (`086` é explícito: "notificação é sempre pessoal"). `mark-read` idempotente
na intenção mas **não** no efeito: segunda chamada retorna `409 NOTIFICATION_ALREADY_READ` (o
contrato documenta esse código explicitamente, diferente de D111/D138's "idempotência silenciosa").

## Auditorias deste lote (candidatas)

1. **Notificação nunca via `POST` direto** — não existe rota de criação no router; só o Dispatcher
   interno cria.
2. **Nunca notifica o próprio ator** — Motorista despachando a própria Viagem via `/commands/start`
   não gera Notificação para si.
3. **Preferência desabilitada bloqueia a criação** — canal `IN_APP` desabilitado por
   `PATCH /channel-preferences/IN_APP` faz o próximo `ViagemDespachada` daquele motorista não gerar
   nenhuma linha em `notificacoes` (verificado por contagem, não só por ausência num `GET`).
3. **Isolamento pessoal** — Gestor com `notification_center.alert.view` não acessa a Notificação de
   outro usuário via ID direto (`403`, nunca `404`).
4. **`mark-read` não é reprocessável como as filas Mobile** — segunda chamada é `409`, contraste
   deliberado com D111/D138, documentado para não confundir os dois padrões de idempotência do
   projeto.

## Achados deste lote

As 5 auditorias candidatas provadas por teste real, despachando uma Viagem de verdade
(`/commands/start`, mesmo caminho que cria o CT-e automaticamente, D396): o Motorista alocado (com
Usuário vinculado) recebe exatamente uma Notificação `ViagemDespachada`; o Gestor, autor da ação,
recebe zero — nunca notificado da própria ação; a Notificação nunca aparece via nenhum `POST`
público, só via o Dispatcher interno; `GET /notifications/{id}` de outro usuário é `403`
(`NOTIFICATION_FORBIDDEN`), nunca `404`; `commands/mark-read` chamado duas vezes devolve `200` na
primeira e `409 NOTIFICATION_ALREADY_READ` na segunda — contraste deliberado com a idempotência
"silenciosa" da Fila de Sincronização Mobile (D111/D138), registrado para não confundir os dois
padrões. Preferência de canal desabilitada (`PATCH .../IN_APP`) provada bloqueando a criação da
próxima Notificação daquele canal — nenhuma linha em `notificacoes`, verificado por contagem.
