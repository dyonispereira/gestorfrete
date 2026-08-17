# SYNC_IMPLEMENTATION.md — Fila de Sincronização, Registro de Sincronização, Assinatura Digital

Fonte: `dictionary/009-app_motorista.md`, `relational/009-app_motorista.md`, `055`-`060`.

## Tabela de despacho — mesmo `Handler`, dois caminhos (D410)

`SYNC_COMMAND_HANDLERS: dict[str, SyncCommandSpec]` mapeia cada `tipo_comando` (`ACCEPT_TRIP`/
`START_TRIP`/`INTERROMPER_TRIP`/`RETOMAR_TRIP`/`FINISH_TRIP`/`REGISTER_OCCURRENCE`/
`REGISTER_DELIVERY`/`REGISTER_POD`) para a MESMA classe `Handler` de `modules/freight` (ou
`modules/mobile`, para `REGISTER_POD`, D411) usada pelos endpoints diretos
`/mobile/trips/{id}/commands/X`. Cada `SyncCommandSpec` sabe construir o `Command` certo a partir do
`payload` JSON genérico do item da fila — nenhuma regra de transição/validação é reimplementada,
só tradução de payload→Command.

## `POST /mobile/sync` — processamento, nunca por ordem de chegada (D298/Auditoria #2)

1. Persiste cada item novo (`INSERT ... ON CONFLICT (sessao_mobile_id, identificador_local_unico)
   DO NOTHING`, D111) — reenvio nunca duplica a linha.
2. Busca todos os itens `PENDENTE`/`FALHOU` da Sessão (incluindo os desta chamada e de chamadas
   anteriores) ordenados por `sequencia_local` — nunca pela ordem em que chegaram nesta requisição.
3. Processa em ordem, um a um; cada item é sua própria unidade de trabalho (falha em um nunca
   impede os demais, D299/D300).
4. Ao final, grava um `RegistroSincronizacao` (nível de lote, D135) com contagens.

## Idempotência (Auditoria #1)

`uq_filas_sincronizacao_identificador_local` é a garantia física. Reenviar o mesmo item (mesmo
`local_id`) nunca gera um segundo `INSERT`; se o item já foi `PROCESSADO`, a resposta ecoa o
resultado já registrado, nunca reprocessa o comando de domínio.

## Conflito (Auditoria #3)

O processamento de cada item captura `ConflictError` (a família de exceção já usada em todo o
backend para "estado atual não permite esta transição", ex. `FREIGHT_TRIP_INVALID_TRANSITION`) —
nunca deixa a exceção propagar. Ao capturar: `status = CONFLITO`, `resolucao_conflito` grava o
motivo (nunca sobrescreve `payload`, D139), e a resposta inclui `conflict.current_state` (reconsulta
o estado atual da entidade afetada) + `conflict.reason`. Qualquer outra exceção de aplicação
(`NotFoundError`/`ValidationError`/`DomainError`) vira `REJEITADO`, com `error` no formato padrão.

## `REGISTER_POD` — três operações já existentes, orquestradas (D411)

1. `RegisterProofOfDeliveryHandler` (`freight`, inalterado) grava `signature_file_id`.
2. `photo_file_id` vira um `Attachment` comum (`shared.collaboration`, `entidade_tipo='canhotos'`) —
   capacidade já genérica (D186/D354), nunca uma coluna nova em `canhotos`.
3. Quando `signature_file_id` presente, uma `DigitalSignature` (`mobile`, aggregate próprio) é
   criada — `documento_tipo=CANHOTO`, `documento_id=<canhoto.id>`, `papel_signatario`,
   `nome_signatario_informado`.

Todas as três já existiam antes deste lote (freight, shared, mobile-dictionary) — `mobile` só as
compõe na mesma transação, nunca decide o efeito de nenhuma.

## Mesmo comando, dois caminhos — a auditoria adicional do usuário

`/mobile/trips/{id}/commands/X` (online, feedback imediato) e `/mobile/sync` (offline, processado
depois) resolvem para o **mesmo objeto de classe** `Handler` — não coincidentemente iguais, mas
literalmente a mesma instância de classe importada de `modules.freight.application.commands.*`
usada nos dois lugares. A prova, no teste, é chamar os dois caminhos com o mesmo estado inicial e
comparar o resultado byte-a-byte, mas a garantia estrutural já vem do código: não há um segundo
`AcceptTripHandler`-para-mobile em lugar nenhum.

## Erros de domínio

`MOBILE_SYNC_UNKNOWN_COMMAND` (400 — `tipo_comando` fora do vocabulário conhecido, D120-style,
nunca aceito silenciosamente), `MOBILE_SYNC_TARGET_NOT_FOUND` (404 — `entidade_destino_id` não
existe ou não pertence ao Motorista da sessão).

## Auditoria e tenant isolation

`FilaSincronizacao`/`RegistroSincronizacao`/`AssinaturaDigital` filtram por
`get_current_tenant_id()`. Cada item processado grava `logs_auditoria` através do `Handler` de
domínio que efetivamente executou (D007) — `mobile` não duplica auditoria do que já é auditado na
origem.
