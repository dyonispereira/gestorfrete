# docs/backend/frota — Sprint 11, Lote 4 (Frota)

Documentação de implementação do bounded context `fleet` (Frota) — primeiro lote de negócio
depois de Cadastros (Lote 3), escolhido por dependência real: `Viagem` (Lote 5, Operação) referencia
`Veículo Tracionador`/`Implemento` diretamente.

| Documento | Cobre |
|---|---|
| [`VEHICLE_IMPLEMENTATION.md`](./VEHICLE_IMPLEMENTATION.md) | `Veículo Tracionador`, `Ficha Técnica`, `Documento do Veículo`, `Categoria de Veículo` |
| [`IMPLEMENT_IMPLEMENTATION.md`](./IMPLEMENT_IMPLEMENTATION.md) | `Implemento` |
| [`COMPOSITION_IMPLEMENTATION.md`](./COMPOSITION_IMPLEMENTATION.md) | `Composição Veicular` |
| [`ODOMETER_IMPLEMENTATION.md`](./ODOMETER_IMPLEMENTATION.md) | `Leitura de Hodômetro` (Time Series) |
| [`AVAILABILITY_IMPLEMENTATION.md`](./AVAILABILITY_IMPLEMENTATION.md) | `Disponibilidade do Veículo` (Read Model) |

Tudo em `modules/fleet/` — bounded context único, RBAC `fleet.*`, sem necessidade de reconciliação
de módulo como em Cadastros (D353): `RBAC_MATRIX.md` §7.8 já atribui as 10 entidades a `fleet`
inteiramente.

## Reconciliação de nomenclatura (D361)

O kickoff do usuário usou "Estado Operacional" e "Configuração" como sub-entidades — nenhuma das
duas existe como tabela/entidade própria em `domain/003-frota.md`/`relational/004-frota.md`:

- **"Configuração"** = a própria `Composição Veicular` (a combinação Veículo+Implemento(s)).
- **"Estado Operacional"** = `Leitura de Hodômetro` (histórico, D083) + `Disponibilidade do Veículo`
  (projeção atual, D081) — dois conceitos já existentes, não um terceiro.

Nenhuma tabela nova criada para esses dois rótulos (D076 — reconciliar antes de duplicar).

## Fora de escopo deste lote, não esquecido (D362)

`Seguradora`/`Apólice de Seguro Veicular`/`Licenciamento do Veículo` — `relational/004-frota.md`
já cria as 3 tabelas fisicamente e `RBAC_MATRIX.md` já tem `fleet.insurance_policy.*`, mas
`020-vehicles.md` já registrava "fora de escopo... não esquecido": nenhum schema `InsurancePolicy`/
`VehicleLicensing` existe em `fleet-schemas.md`, nenhum endpoint em `020-025`. D332 proíbe
implementar sem contrato — as 3 tabelas também não entram nesta migration (nenhum consumidor real
neste lote).

## Categoria de Veículo — implementada sem endpoint HTTP (D363)

`categoria_veiculo_id` é `NOT NULL` em `veiculos_tracionadores`/`implementos` — tem que existir
fisicamente para o lote funcionar, mas nenhum arquivo `docs/api/0NN-vehicle-categories.md` existe
apesar de `RBAC_MATRIX.md` já ter `fleet.vehicle_category.*`. Implementada como tabela + Repository
interno (sem Command/Query/Router); seed direto via Repository nos testes de integração — mesmo
padrão já usado para `permissoes` (Lote 2/3).

## Disponibilidade do Veículo é só leitura (auditoria pedida pelo usuário)

Antes de fechar o lote, confirmar que `disponibilidade_veiculo` não tem **nenhum** caminho de
escrita: nenhum endpoint (`020-025` nunca tem `POST`/`PATCH`/`DELETE` para ela, D247), nenhum
CommandHandler, nenhum método público de escrita no Repository além do usado internamente pelo
projetor de eventos. Ver [`AVAILABILITY_IMPLEMENTATION.md`](./AVAILABILITY_IMPLEMENTATION.md).

## Composição vigente é única por veículo (auditoria pedida pelo usuário)

`uq_composicoes_veiculares_vigente` (índice único parcial em `composicoes_veiculares` WHERE
`data_fim_vigencia IS NULL`) é a fonte de verdade física — mas o teste de integração prova isso via
HTTP real (criar duas composições para o mesmo veículo, confirmar que a primeira foi fechada
automaticamente, nunca duas vigentes simultâneas), não só assume que o índice existe. Ver
[`COMPOSITION_IMPLEMENTATION.md`](./COMPOSITION_IMPLEMENTATION.md).

## Gaps corrigidos antes do código

- **D366** — `EVENT_MAP.md` não tinha seção `fleet`, apesar de `domain/003-frota.md` já nomear 7
  eventos "novos" desde o Sprint 09. Seção adicionada.
- **D367** — `DEPENDENCY_MAP.md` não listava Composição Veicular/Documento do
  Veículo/Hodômetro/Disponibilidade/Categoria/Licenciamento. Linhas adicionadas às Camadas 0-2.

## FKs adiadas (mesmo padrão de D355)

- `veiculos_tracionadores.filial_id` — `Filial` (`tenancy`) ainda não existe fisicamente no
  backend (só `Tenant`, Lote 2). Coluna nullable, sem `REFERENCES` ainda.
- `leituras_hodometro.viagem_id` — `Viagem` (`freight`) é Lote 5+. Coluna nullable, sem
  `REFERENCES` ainda.
- `documentos_veiculo.arquivo_id` — `arquivos` (`storage`) ainda não implementado. Mesma situação
  de `documentos_motorista.arquivo_id` (Lote 3).

## Critério de Definição de Pronto (D352)

Nenhum agregado é considerado concluído sem: migration real, Repository testado, Application
testado, E2E via HTTP, tenant isolation + auditoria comprovados por teste — mais, pedido explícito
do usuário para este lote: teste dedicado da vigência única de Composição Veicular e auditoria de
que Disponibilidade do Veículo não tem caminho de escrita.

## Achados deste lote (Sprint 11, Lote 4)

`alembic upgrade head` criou as 9 tabelas novas (`categorias_veiculo`, `implementos`,
`veiculos_tracionadores`, `composicoes_veiculares` + tabela de junção
`composicoes_veiculares_implementos`, `disponibilidade_veiculo`, `documentos_veiculo`,
`fichas_tecnicas_veiculo`, `leituras_hodometro` particionada + `leituras_hodometro_default`) contra
o Postgres portátil sem erros de aplicação — confirmado por `psql \dt`/`\d` (28 tabelas totais, FKs,
o índice único parcial `uq_composicoes_veiculares_vigente` e o `CHECK` de vigência todos presentes).
Diferente do Lote 3, nenhum bug de produção novo foi encontrado por execução: as duas lições do lote
anterior (D357 — sempre declarar `ForeignKey("tenants.id")`; D360 — remover manualmente o
`op.drop_table('logs_auditoria_default')` que o autogenerate sempre propõe por falso positivo) foram
aplicadas de forma proativa desde o primeiro rascunho de cada model/migration, não descobertas por um
teste falhando.

`ruff check src`, `mypy src` (770 arquivos, `strict = true`) e `lint-imports` (9/9 contratos, os 2
combinados de domain-purity/application-never-imports-interfaces agora cobrindo também
`modules.fleet.*`) passaram limpos na primeira execução.

A suíte nova, `tests/integration/test_frota_flow.py` (10 testes), cobre os 5 agregados via HTTP real
e as duas auditorias pedidas explicitamente pelo usuário antes do fechamento:

- **Disponibilidade sem caminho de escrita** — `GET /veiculos/{id}/disponibilidade` antes de
  qualquer evento retorna `404 FLEET_VEHICLE_AVAILABILITY_NOT_FOUND`; `POST`/`PATCH`/`DELETE` em
  `/veiculos/{id}/disponibilidade` e `POST /veiculos/disponibilidade` retornam `405` — prova de que
  as rotas nunca foram registradas, não apenas que retornam erro de permissão. Só depois de chamar
  `VehicleAvailabilityProjector.apply_trip_dispatched(...)` diretamente (simulando o futuro
  consumidor real de `ViagemDespachada`) a mesma consulta passa a `200`.
- **Composição vigente única por veículo** — três composições sucessivas para o mesmo veículo,
  consultando `SELECT COUNT(*) WHERE data_fim_vigencia IS NULL` diretamente no banco depois de cada
  chamada HTTP: nunca mais que 1 linha em nenhum passo, não apenas confiando no índice único parcial.

Um achado real, mas de **autoria do teste**, não do código de produção: a primeira versão do teste de
Disponibilidade chamava `apply_trip_dispatched` com um `driver_id` aleatório — `disponibilidade_
veiculo.motorista_atual_id` tem `ForeignKey("motoristas.id")` real, então a chamada falhava com
`ForeignKeyViolationError`. Corrigido criando um Motorista real via `POST /drivers` (Lote 3) antes de
simular o evento — o comportamento do FK está correto, o teste que precisava de dado real.

Resultado agregado final (unit + integration juntos, excluindo apenas Redis/RabbitMQ/MinIO — infra
ausente deste sandbox, não relacionada a este lote): **78 passed, 0 failed** (48 unitários + 10 de
`identity_access`/`tenancy` + 9 de Cadastros + 10 de Frota + 1 de conectividade Postgres). Detalhe em
[`../TESTING_STRATEGY.md`](../TESTING_STRATEGY.md#sprint-11-lote-4--frota-validação-com-postgresql-real).

## Decisões

D361–D368 — ver [`../../product/DECISIONS.md`](../../product/DECISIONS.md).

## Como esta pasta cresce

Um lote por vez. Próximo, pela ordem confirmada pelo usuário: Sprint 11 Lote 5 — Operação/Viagens.
