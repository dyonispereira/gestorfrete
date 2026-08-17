# docs/backend/operacao — Sprint 11, Lote 5 (Operação/Viagens)

Documentação de implementação do bounded context `freight` (Operação) — o core domain do
GestorFrete (`flows/002-VIAGEM.md`). Escopo confirmado pelo usuário: exclusivamente o agregado
`Viagem`, sem misturar Cotação/Contrato de Frete/Solicitação de Frete/Tabela de Preço (um próximo
core domain a montar) nem Coleta/Romaneio (sem endpoint neste lote, ver D370).

| Documento | Cobre |
|---|---|
| [`TRIP_IMPLEMENTATION.md`](./TRIP_IMPLEMENTATION.md) | `Viagem` (agregado raiz), as três dimensões de status, `ENCERRADA`, Snapshots, `Alocação de Recurso da Viagem` |
| [`DELIVERY_IMPLEMENTATION.md`](./DELIVERY_IMPLEMENTATION.md) | `Entrega` (multi-drop), `Janela de Entrega`, `Canhoto` |
| [`OCCURRENCE_IMPLEMENTATION.md`](./OCCURRENCE_IMPLEMENTATION.md) | `Ocorrência` |
| [`TIMELINE_IMPLEMENTATION.md`](./TIMELINE_IMPLEMENTATION.md) | Timeline da Viagem (Read Model, consulta) |

Tudo em `modules/freight/` — bounded context único, RBAC `freight.*` (§7.12/7.13).

## Escopo físico deste lote (D370)

`relational/003-operacao.md` modela 19 tabelas; só 9 têm consumidor real em `014-trips.md` a
`019-trip-timeline.md` e são criadas nesta migration: `viagens`, `viagem_status_history`,
`alocacoes_recurso_viagem`, `entregas`, `janelas_entrega`, `canhotos`, `ocorrencias`, `anexos`,
`comentarios`.

**Fora deste lote, não esquecido**: `pontos_parada_viagem`/`coletas`/`romaneios`/`itens_carga`
(Coleta/Romaneio documentados como "Externa, fora de escopo" em `015`/`018` — sem endpoint, duas
transições da máquina de estados inalcançáveis via API até esse lote existir);
`contratos_frete`/`cotacoes`/`itens_cotacao`/`solicitacoes_frete`/`tabelas_preco`/
`itens_tabela_preco` (nenhum dos 6 arquivos de API deste lote os expõe — Cotação/Pricing é o
próximo core domain). `viagens.tabela_preco_aplicada_snapshot_id` nasce sem FK física (D355/D362).

## Reconciliação de vocabulário (D369)

O kickoff citou as três dimensões como "operacional, logística, financeira" — o modelo já
congelado (D020) define Operacional/**Fiscal**/Financeiro. Implementadas exatamente as três
congeladas; "logística" tratado como paráfrase informal de "Fiscal", nunca uma quarta dimensão.

## Anexos/Comentários — infraestrutura sem endpoint HTTP (D371)

`anexos`/`comentarios` (D186, compartilhados por todo agregado futuro com "Anexos suportados"/
"Comentários suportados") nascem fisicamente pela primeira vez neste lote — Viagem é a primeira
entidade que precisa deles. Implementados como tabela + Repository interno, sem Command/Query/
Router: `015-trip-deliveries.md` e `019-trip-timeline.md` confirmam que nenhum contrato de API
existe ainda para eles (mesmo padrão de D363).

## Timeline — escopo mais estreito que o prometido em `002-VIAGEM.md` (D372)

`GET /viagens/{id}/timeline` implementa só o que `019-trip-timeline.md` já define como real para
este lote: `viagem_status_history` + `ocorrencias`, cursor-paginado. Checklist/Abastecimento/OS/
Documento Fiscal/Anexos/Comentários ficam de fora — nenhum tem endpoint de API ainda.

## Canhoto incluído apesar de não estar na lista literal de "Entidades internas" (D373)

`015-trip-deliveries.md`'s `POST .../canhoto` e a pré-condição do comando `finish` ("todos os
Canhotos correspondentes registrados") exigem a entidade — sem ela, "concluir" (pedido
explicitamente pelo usuário) não seria implementável como o contrato já define.

## Duas auditorias pedidas explicitamente pelo usuário antes de fechar o lote

1. **`encerrada == GENERATED`**: provar por teste que a aplicação nunca escreve nessa coluna, o
   banco calcula sozinho, e qualquer tentativa de escrita direta falha. Ver
   [`TRIP_IMPLEMENTATION.md`](./TRIP_IMPLEMENTATION.md#encerrada-d019d020).
2. **Snapshots congelados**: criar Viagem, alterar Cliente/Motorista depois, consultar a Viagem,
   provar que os snapshots continuam exatamente iguais ao momento em que foram capturados. Ver
   [`TRIP_IMPLEMENTATION.md`](./TRIP_IMPLEMENTATION.md#snapshots-d038d071d073).

## Transições sem gatilho HTTP neste lote (D376)

`RASCUNHO→PLANEJADA→AGUARDANDO_CHECKLIST` (cascata automática na primeira alocação),
`AGUARDANDO_CHECKLIST→LIBERADA` (Checklist), `EM_DESLOCAMENTO→CARREGANDO` (Coleta),
`CARREGANDO→EM_TRANSITO` (Romaneio) — as três últimas sem endpoint próprio neste lote nem em
nenhum anterior. Implementadas como métodos internos do agregado `Trip`, nunca uma rota HTTP,
mesmo padrão do Projetor de Disponibilidade (D247, Lote 4) — testes chamam esses métodos
diretamente para simular o futuro consumidor de evento e alcançar `LIBERADA`/`EM_TRANSITO`.

## Gap sinalizado, não implementado: `Idempotency-Key` (D380)

6 endpoints deste lote declaram `Idempotency-Key` obrigatória (D211) — mas nenhuma infraestrutura
HTTP de idempotência existe em nenhum lote anterior (nenhuma tabela, nenhum middleware). É uma
preocupação transversal, não específica de `freight`; implementá-la agora expandiria escopo para
uma peça de infraestrutura que merece seu próprio design (armazenamento, TTL, hash de payload).
Sinalizado com destaque, não implementado nem silenciosamente ignorado — decisão de priorização
fica para o usuário.

## Critério de Definição de Pronto (D352)

Migration real, Repository testado, Application testado, E2E via HTTP, tenant isolation +
auditoria comprovados por teste — mais as duas auditorias explícitas acima.

## Achados deste lote (Sprint 11, Lote 5)

`alembic upgrade head` criou as 9 tabelas novas (`viagens`, `viagem_status_history` particionada +
`viagem_status_history_default`, `alocacoes_recurso_viagem`, `entregas`, `janelas_entrega`,
`canhotos`, `ocorrencias`, `anexos`, `comentarios`) contra o Postgres portátil sem erros de
aplicação — confirmado por `psql \dt`/`\d viagens` (38 tabelas totais, os dois `GENERATED ALWAYS AS
(...) STORED` de `encerrada`/`margem_prevista` presentes e corretos, todas as FKs reais para
`clientes`/`motoristas`/`veiculos_tracionadores`/`implementos` já existentes dos Lotes 3/4).

`ruff check src`, `mypy src` (862 arquivos, `strict = true`) e `lint-imports` (9/9 contratos, os 2
combinados agora cobrindo `modules.freight.*`/`shared.collaboration.*`) passaram limpos.

A suíte nova, `tests/integration/test_operacao_flow.py` (15 testes), cobre o agregado `Trip` de
ponta a ponta — criação, alocação de recursos (D188), toda a máquina de estados operacional
(`accept`/`dispatch`/`start`/`interromper`/`retomar`/`cancelar`/`finish`/`close-administrative`),
Entrega + Canhoto, Ocorrência, Timeline — mais as duas auditorias pedidas explicitamente pelo
usuário antes do fechamento:

1. **`encerrada` é `GENERATED`, nunca escrita pela aplicação** — um `UPDATE` direto via SQL bruto
   falha com o erro nativo do Postgres para coluna `GENERATED ALWAYS`; avançar as três dimensões
   via `TripInternalTransitions` (D375/D376) até seus estados terminais faz `encerrada` virar
   `true` sozinha, sem que nenhum código da aplicação a tenha escrito — testado passo a passo
   (Fiscal converge primeiro, `closed` continua `false`; só depois que Financeiro também converge,
   `closed` vira `true`).
2. **Snapshots nunca ressincronizam** — cria Viagem (congela `cliente_snapshot`), despacha (congela
   `nome_motorista_snapshot`/`placa_veiculo_snapshot`), renomeia o Cliente e o Motorista de origem
   via seus próprios módulos (`PATCH /clients`, `PATCH /drivers`), consulta a Viagem de novo:
   os três valores continuam exatamente iguais ao momento da captura.

Dois achados reais rodando a suíte pela primeira vez, ambos de implementação (não de teste):

- **D382** — `TripModel.encerrada`/`.margem_prevista`, mapeadas como colunas comuns, faziam todo
  `INSERT`/`UPDATE` incluir seus valores Python-side (`False`/`None`) mesmo sem o Repository jamais
  as atribuir — o SQLAlchemy ORM inclui por padrão toda coluna mapeada na instrução, e o Postgres
  rejeita qualquer escrita explícita em coluna `GENERATED ALWAYS`. Corrigido com
  `sqlalchemy.Computed(...)`, que instrui o ORM a nunca incluí-las e a recuperá-las de volta via
  `RETURNING`. Primeira coluna `GENERATED STORED` deste backend mapeada no ORM (as anteriores,
  `logs_auditoria`/`leituras_hodometro`, só tinham particionamento via SQL bruto, não uma coluna
  gerada mapeada).
- **D383** — a suíte completa (unit + integration) revelou que `test_infrastructure_connectivity.py`
  era o único arquivo de teste de integração sem a fixture `_fresh_engine_per_test`/
  `dispose_engine()` que todo outro já tem — um bug pré-existente desde o Lote 2, nunca exposto
  porque nenhum arquivo de teste anterior a este lote vinha depois dele em ordem alfabética.
  Corrigido no arquivo, não no código de produção.

Também confirmado durante a auditoria de escopo, antes de escrever qualquer código: dois pontos de
design genuinamente ambíguos na máquina de estados congelada foram resolvidos e documentados como
reconciliações (D376/D378), nunca inventados silenciosamente — ver `TRIP_IMPLEMENTATION.md`.

Resultado agregado final (unit + integration juntos, excluindo apenas Redis/RabbitMQ/MinIO — infra
ausente deste sandbox, não relacionada a este lote): **93 passed, 0 failed** (48 unitários + 10 de
`identity_access`/`tenancy` + 9 de Cadastros + 10 de Frota + 15 de Operação + 1 de conectividade
Postgres). Detalhe em
[`../TESTING_STRATEGY.md`](../TESTING_STRATEGY.md#sprint-11-lote-5--operaçãoviagens-validação-com-postgresql-real).

## Decisões

D369–D383 — ver [`../../product/DECISIONS.md`](../../product/DECISIONS.md).

## Como esta pasta cresce

Um lote por vez. Próximo, pela ordem confirmada pelo usuário: Sprint 11 Lote 6 — Financeiro.
