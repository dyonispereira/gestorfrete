# docs/backend/transversais — Sprint 11, Lote 10 (Recursos Transversais)

Documentação de implementação dos últimos bounded contexts com contrato OpenAPI congelado e ainda
sem Backend real: `storage` (File/Attachment/Comment), busca global e Timeline Universal (sem
bounded context próprio), `notification_center` (Notificação/Preferência de Canal) e `integration`
(Configuração de Integração/Webhook/Execução de Job). BI (`062`-`070`) e IA (`071`-`077`) foram
explicitamente adiados pelo usuário para um sprint futuro — este lote cobre exatamente `078` a `089`,
com a exceção de `084`/`085` (Relatórios/Exportações), que são documentos de reconciliação puros sem
endpoint próprio (D326) e por isso não geram nenhum código neste lote.

| Documento | Cobre |
|---|---|
| [`STORAGE_IMPLEMENTATION.md`](./STORAGE_IMPLEMENTATION.md) | `File`/upload-download via MinIO real (D412), `078`/`079` |
| [`COLLABORATION_IMPLEMENTATION.md`](./COLLABORATION_IMPLEMENTATION.md) | `Attachment`/`Comment` sobre Viagem (`080`/`081`), Busca Global (`082`), extensão da Timeline (`083`) |
| [`NOTIFICATION_IMPLEMENTATION.md`](./NOTIFICATION_IMPLEMENTATION.md) | `Notificação`/`Preferência de Canal` (`086`), conjunto mínimo de 2 eventos (D414) |
| [`INTEGRATION_IMPLEMENTATION.md`](./INTEGRATION_IMPLEMENTATION.md) | `Configuração de Integração`/`Webhook`/`Execução de Job` (`087`/`088`/`089`) |

## Este lote não é um bounded context, são quatro pequenos

Ao contrário de todo lote anterior (um domínio central, ex.: Viagem, CT-e, Rastreamento), Recursos
Transversais é uma coleção de capacidades de infraestrutura de produto que várias entidades
consomem — cada uma pequena o suficiente para não justificar seu próprio lote isolado, mas juntas
fecham o conjunto de contratos ainda sem Backend. `storage`/`notification_center`/`integration` são
três bounded contexts reais (D215); Busca Global e Timeline não têm bounded context próprio — são
compositores finos de leitura sobre módulos já existentes (D317/D318).

## Achado central antes de qualquer código: nem tudo aqui é trabalho novo

- **`084`/`085` não entram neste lote** — reconciliados com `SavedReport`/`Export` (Lote 11, BI),
  que o usuário adiou. Zero endpoint próprio, D326.
- **`Attachment`/`Comment` já existem como Entity + Repository reais** desde o Lote 5 (Operação,
  D371) — usados inclusive pelo Canhoto do Mobile (Lote 9). Este lote adiciona a camada HTTP sobre
  `Viagem` (único dono ativado, D316) — nunca reimplementa a entidade.
- **Storage é o primeiro lote com I/O binário real** — `arquivo_id` sempre foi referência lógica
  nunca resolvida de verdade em nenhum lote anterior. D412: MinIO instalado como binário portátil
  standalone (sem Docker, indisponível neste ambiente desde o Lote 1) para que isso seja testável
  contra infraestrutura real, mesmo espírito do PostGIS no Lote 8.

## Critério de Definição de Pronto (D352)

Migration real, Repository testado, Application testado, E2E via HTTP, tenant isolation + auditoria
comprovados por teste — aplicado a cada um dos 4 documentos acima. Auditorias específicas de cada
subsistema estão documentadas no respectivo arquivo.

## Decisões

D412–D414 (e quaisquer achados adicionais deste lote) — ver
[`../../product/DECISIONS.md`](../../product/DECISIONS.md).

## Achados deste lote (Sprint 11, Lote 10)

Migration aplicada com sucesso na primeira tentativa — 6 tabelas novas (`arquivos`,
`configuracoes_integracao`, `webhooks`, `execucoes_job`, `notificacoes`, `preferencias_
notificacao`), incluindo a chave primária composta `(id, data_hora_inicio)` de `execucoes_job`
(particionada, mesma disciplina de `logs_auditoria`/`eventos_fiscais`) resolvida corretamente de
primeira, sem precisar de uma falha real para descobrir — lição dos Lotes 2/7/8 aplicada
proativamente. Suíte final: **168 passed, 0 failed** (11 novos testes em
`test_transversais_flow.py`, todos passando na primeira execução real — os 6 subsistemas deste
lote, incluindo I/O binário genuíno contra MinIO, funcionaram de primeira). `ruff`, `mypy --strict`
(1326 arquivos) e os 10 contratos de `import-linter` (com `storage`/`notification_center`/
`integration` adicionados aos dois contratos combinados) passam limpos no repositório inteiro.

Dois achados arquiteturais reais, cada um com decisão registrada (ver seção "Decisões" abaixo):
D415 (Storage precisa materializar `File` no `POST /uploads`, não em `commands/complete`, porque
`arquivos_status_enum` não tem estado intermediário) e D417 (`Busca Global` exclui `ordem_servico`
porque `Ordem de Serviço` nunca foi implementada no Backend — só `Fornecedor` existe em
`modules/maintenance/`, apesar do contrato `082-global-search.md` listar o tipo).

**Regressão real encontrada e corrigida, fora do escopo deste lote mas causada por ele**: como
`CreateOccurrenceHandler`/`DispatchTripHandler` (`freight`, já existentes desde os Lotes 4/5) agora
criam `Notificação` (D414), o `_cleanup_tenant` de `test_mobile_flow.py` (Lote 9) — que nunca
conheceu a tabela `notificacoes` — passou a violar uma FK ao tentar apagar `usuarios` antes de
`notificacoes`. Corrigido adicionando a limpeza de `notificacoes`/`preferencias_notificacao` a esse
arquivo (os outros três arquivos que também despacham Viagem/criam Ocorrência —
`test_financeiro_flow.py`/`test_fiscal_flow.py`/`test_operacao_flow.py` — foram checados
individualmente e não foram afetados). A mesma falha de teardown deixou dados de tenant órfãos no
Postgres entre execuções, o que por sua vez expôs um segundo bug real, pré-existente: a própria
asserção de `TestConflictAudit` (Lote 9) consultava `filas_sincronizacao` só por
`identificador_local_unico`, sem filtrar por `tenant_id` — inofensivo enquanto nunca havia dado
órfão com o mesmo literal, mas produziu `MultipleResultsFound` assim que um tenant órfão de uma
execução anterior colidiu com o literal `"cmd-finish-conflict"` de uma execução nova. Corrigido
adicionando o filtro de tenant que sempre devia ter existido — achado clássico de "a suíte inteira
protege a suíte inteira", exatamente o tipo de regressão cross-lote que rodar a suíte completa (não
só o arquivo novo) existe para capturar.

## Como esta pasta cresce

Único lote restante com contrato OpenAPI congelado e sem Backend. Depois deste, o Backend de domínio
fica pausado até o usuário decidir retomar BI/IA ou abrir uma sprint de OpenAPI nova (Pricing/
Routing, sem contrato ainda) — ou pivotar para o Frontend, cujo contrato já está estável desde a
Sprint 10.
