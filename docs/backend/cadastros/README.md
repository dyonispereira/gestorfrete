# docs/backend/cadastros — Sprint 11, Lote 3 (Cadastros)

Documentação de implementação dos primeiros bounded contexts de negócio construídos sobre a
Foundation/Core (Sprint 11, Lotes 1/1.1/2). "Cadastros" é o nome deste **lote**, nunca de um módulo
de código — ver D353: os 7 agregados abaixo já pertencem, pelo RBAC congelado, a 5 bounded contexts
diferentes e existentes.

| Documento | Bounded context (código) | Cobre |
|---|---|---|
| [`ADDRESS_IMPLEMENTATION.md`](./ADDRESS_IMPLEMENTATION.md) | `shared/` (componente compartilhado, D354) | `Endereço` — usado por `crm` e `maintenance` |
| [`CLIENT_IMPLEMENTATION.md`](./CLIENT_IMPLEMENTATION.md) | `modules/crm/` | `Cliente`, `Contato do Cliente` |
| [`SUPPLIER_IMPLEMENTATION.md`](./SUPPLIER_IMPLEMENTATION.md) | `modules/maintenance/` | `Fornecedor` |
| [`DRIVER_IMPLEMENTATION.md`](./DRIVER_IMPLEMENTATION.md) | `modules/drivers/` | `Motorista`, `Documento do Motorista` |
| [`EMPLOYEE_IMPLEMENTATION.md`](./EMPLOYEE_IMPLEMENTATION.md) | `modules/identity_access/` | `Funcionário` (novo agregado no módulo já existente do Lote 2) |
| [`COST_CENTER_IMPLEMENTATION.md`](./COST_CENTER_IMPLEMENTATION.md) | `modules/financial/` | `Centro de Custo` |

## Por que não existe `modules/cadastros/`

`docs/domain/001-cadastros.md`/`docs/database/relational/002-cadastros.md` agrupam estas entidades
só para fins de leitura — nunca foram um bounded context. `RBAC_MATRIX.md` (fonte de verdade, D334)
já atribui cada uma a um dono real: Cliente/Contato → `crm`; Fornecedor → `maintenance`;
Motorista/Documento → `drivers`; Funcionário → `identity_access`; Centro de Custo → `financial`.
Criar uma pasta `modules/cadastros/` violaria D334/D335 (só bounded contexts com correspondência
real entram em `modules/`). Decisão confirmada com o usuário antes de escrever qualquer código
(D353).

## Endereço é compartilhado, não duplicado (D354)

`Endereço` (tabela física `enderecos`, polimórfica) não tem RBAC própria — é sub-recurso de
Cliente/Fornecedor/Filial, sempre autorizado pela permissão do dono (`crm.client.edit`,
`maintenance.supplier.edit`, etc.). Implementado uma única vez em `apps/api/src/shared/addresses/`,
um pacote novo, irmão de `core/`/`shared_kernel/`/`modules/`/`interfaces/`, reservado a
componentes de negócio compartilhados sem bounded context/RBAC próprio. `crm`/`maintenance` (e
futuramente `tenancy`, quando `Filial` for implementada) importam o `AddressRepository`
compartilhado — nenhum módulo reimplementa Endereço internamente.

Filial **não** ganha suporte a Endereço neste lote — `Filial`/`Branch` (bounded context `tenancy`,
contrato já congelado em `006-branches.md`) não foi pedida pelo usuário para este lote e não existe
ainda no backend (só `Tenant` existe, Lote 2). `enderecos_entidade_tipo_enum` já inclui `FILIAL`
fisicamente (D231); o dia em que `Filial` for implementada, ela só precisa injetar o mesmo
`AddressRepository`, sem nenhuma mudança em `shared/addresses/`.

## Regra de dependência: `shared/` segue o mesmo padrão de `core/`

`shared/` nunca importa `modules/`/`interfaces/` (mesmo contrato de `core`, ver
[`../DEPENDENCY_RULES.md`](../DEPENDENCY_RULES.md)); ao contrário de `core/`, `shared/` **pode**
depender de `core.database`/`core.multitenancy` (é infraestrutura real com sessão/tenant, não
vocabulário puro) — a diferença entre os dois é semântica (infraestrutura técnica vs. componente de
negócio compartilhado), não posição na árvore de dependência.

## Gaps reais encontrados e resolvidos antes do código (D355)

`centros_custo.filial_id` referencia `filiais(id)` na DDL congelada — mas `Filial` (bounded context
`tenancy`) não existe fisicamente ainda (só `Tenant`, Lote 2). Mesma natureza de D196 (referência
documentada sem `CREATE TABLE` correspondente). Resolvido como D250: a coluna nasce `UUID` nullable,
sem `REFERENCES` físico; a constraint é adicionada numa migration futura, quando `Filial` existir.
Detalhe em [`COST_CENTER_IMPLEMENTATION.md`](./COST_CENTER_IMPLEMENTATION.md).

## Critério de Definição de Pronto (D352) — aplicado a cada um dos 7 agregados

Nenhum agregado abaixo é considerado concluído sem: (1) migration aplicada em PostgreSQL real; (2)
Repository com teste de integração contra banco real; (3) serviço de Application testado; (4)
endpoint exercitado E2E via HTTP real; (5) auditoria e isolamento por tenant comprovados por teste.

## Achados deste lote (Sprint 11, Lote 3)

Encontrados só por execução real (nunca por inspeção de código) — cada um virou uma linha em
`DECISIONS.md`:

| # | Achado | Decisão |
|---|---|---|
| 1 | `DEPENDENCY_RULES.md` proibia leitura cross-module Application→Infrastructure, mas o próprio `GetMeHandler` do Lote 2 já fazia isso — regra corrigida para bater com o código | D356 |
| 2 | 7 dos 8 novos models nasceram sem `ForeignKey("tenants.id")` em `tenant_id` (só `EmployeeModel` copiou o padrão certo) — corrigido antes da migration | D357 |
| 3 | `CreateAddressHandler`/`UpdateAddressHandler` não capturavam a violação do índice único parcial — `Repository.add()` já faz `flush()`, escapando do `try` em volta só de `uow.commit()` | D358 |
| 4 | `PATCH /users/{id}` (Lote 2) não expõe `employee_id`/`driver_id` — gap pré-existente, documentado, não corrigido (fora de escopo) | D359 |
| 5 | `alembic revision --autogenerate` sempre marca `logs_auditoria_default` como "removida" (partição real, invisível ao ORM) — remover a linha manualmente é obrigatório em toda migration futura | D360 |

## Estado final verificado

`ruff check src`, `mypy src` (687 arquivos, `strict`) e `lint-imports` (9/9 contratos, incluindo os
2 novos de `crm`/`maintenance`/`drivers`/`financial`/`shared.addresses`) — todos `PASS`. `pytest`
completo (unit + integration, exceto Redis/RabbitMQ/MinIO, ausentes deste sandbox): **68 passed, 0
failed**, incluindo os 9 testes novos de Cadastros (CRUD completo dos 5 agregados + sub-recursos
Endereço/Contato/Documento via HTTP real, tenant isolation, auditoria, `block`/`unblock`,
duplicidade de documento/CNPJ/código contábil, vínculo Funcionário↔Usuário ativo).

## Decisões

D353–D360 — ver [`../../product/DECISIONS.md`](../../product/DECISIONS.md).

## Como esta pasta cresce

Um lote por vez, mesmo princípio do resto do projeto. Próximo bounded context de negócio (Sprint 11
Lote 4+) segue a ordem confirmada pelo usuário: Frota → Operação/Viagens → Financeiro → Fiscal →
Rastreamento → Mobile → BI → IA.
