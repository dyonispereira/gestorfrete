# DEPENDENCY_RULES.md — A Regra de Dependência, Aplicada Mecanicamente

Seção crítica, pedida explicitamente pelo usuário. A regra em prosa (`docs/architecture/
clean-architecture.md`) já existia desde a Fase 0 — o que este lote adiciona é **fazer valer**:
um build que viola a regra falha, não passa "porque o código parece certo".

## A regra, em uma frase

```
Interfaces → Application → Domain
Infrastructure implementa interfaces que as camadas internas declaram — nunca o contrário.
```

Nunca:

```
Domain → SQLAlchemy      (Domain não sabe que existe banco)
Domain → FastAPI          (Domain não sabe que existe HTTP)
Application → HTTP          (Application não sabe que existe FastAPI/Starlette)
core/ → modules/ ou interfaces/  (infraestrutura transversal nunca conhece regra de negócio nem HTTP)
```

## Ferramenta: `import-linter` (`pyproject.toml`, `[tool.importlinter]`)

Instalado como dependência de desenvolvimento (`import-linter = "^2.13"`), executado via
`lint-imports` (com `PYTHONPATH=src`, mesmo padrão de `pytest`/`mypy`/`ruff` já configurados). Falha
o processo com código de saída não-zero e lista exatamente qual import viola qual contrato — não é
uma checagem manual nem uma convenção de code review, é um gate mecânico.

### Contratos ativos hoje (4, todos verificados `KEPT`)

| Contrato | Tipo | Garante |
|---|---|---|
| "Shared Kernel has zero dependents among its own dependencies" | `independence` | `shared_kernel/domain`, `shared_kernel/application`, `shared_kernel/infrastructure` não dependem uns dos outros de forma cruzada indevida |
| "Shared Kernel never imports core, modules or interfaces" | `forbidden` | O building block mais interno do sistema nunca depende de nada — nem da própria infraestrutura transversal |
| "Core (cross-cutting infrastructure) never imports modules or interfaces" | `forbidden` | `core/` nunca sabe que um bounded context ou o HTTP existem |
| "Composition root: interfaces depends on core, core never depends on interfaces" | `layers` | A direção clássica de Clean Architecture entre a camada mais externa e a infraestrutura transversal |

**Verificação de que o gate realmente pega uma violação** (não apenas passa vazio): durante este
lote, foi injetado deliberadamente um import de `interfaces.api.health` dentro de
`core/config/settings.py` — `lint-imports` imediatamente reportou `BROKEN` nos dois contratos
relevantes, com o import exato e o número da linha. O import foi revertido em seguida; o exercício
existe só para provar que o gate funciona, não para ficar no código.

```
$ PYTHONPATH=src lint-imports
Core (cross-cutting infrastructure) never imports modules or interfaces  BROKEN
  core is not allowed to import interfaces:
  - core.config.settings -> interfaces.api.health (l.65)
```

### Carve-out deliberado — `domain` pode importar `core.exceptions` e `core.security.ports`

Registrado ao escrever o primeiro código de negócio real (Sprint 11, Lote 2): `core/exceptions/
base.py` (`DomainError`/`ConflictError`/`NotFoundError`/...) é Python puro — zero import de
FastAPI/SQLAlchemy/qualquer framework — e existe precisamente para ser o vocabulário de erro comum
entre Domain e o mapeamento HTTP (`ERROR_HANDLING.md`); `core/security/ports.py` é só `Protocol`s
(`PasswordHasher`/`TokenService`), sem implementação. Exigir que cada bounded context reimplemente
sua própria hierarquia de exceções de domínio, só para depois traduzi-la em `core.exceptions` na
Application, adicionaria uma camada de tradução sem benefício real neste estágio do projeto —
avaliado e aceito conscientemente, não uma violação não percebida. **Continua proibido**: `domain`
importar `core.database`/`core.messaging`/`core.cache`/`core.storage`/`core.observability` (essas
são infraestrutura real, com efeito colateral) ou qualquer coisa de `core.security` além do
`ports.py` (nunca `JWTTokenService`/`BcryptPasswordHasher` concretos dentro de `domain` — só a
Application os injeta).

### Contratos por bounded context (ativos desde que `identity_access`/`tenancy` ganharam código real)

| Contrato | Tipo | Garante |
|---|---|---|
| "`tenancy`/`identity_access` domain never imports infra-with-side-effects" | `forbidden` | `modules.tenancy.domain`/`modules.identity_access.domain` nunca importam `core.database`/`.messaging`/`.cache`/`.storage`/`.observability`, nem `infrastructure`/`interfaces` do próprio módulo |
| "`tenancy`/`identity_access` application never imports interfaces" | `forbidden` | Application nunca importa a camada HTTP (`interfaces/`) do próprio módulo — a dependência é sempre Interfaces → Application, nunca o inverso |

**Nota sobre Application → Infrastructure (mesmo módulo)**: diferente da regra "textbook" de Clean
Architecture (Application só depende de Protocol, Infrastructure injetada de fora), os
`CommandHandler`s deste lote **constroem sua própria `SQLAlchemyUnitOfWork` e o Repository
concreto correspondente internamente** — o mesmo padrão explícito no pedido do usuário ("Use Case →
UnitOfWork → Repository, Repository, commit"). Isso significa Application importa uma classe
concreta de `infrastructure/persistence/repositories/` do **mesmo módulo** — aceito
deliberadamente (documentado aqui, não uma exceção não percebida) porque o UnitOfWork já é, por
natureza, uma decisão de Application sobre a fronteira transacional, não algo injetável de fora sem
perder a garantia de atomicidade.

**Correção (D356, Sprint 11 Lote 3)**: esta nota afirmava até aqui "nunca aceito entre módulos
diferentes — nenhum Application importa infrastructure de outro bounded context", mas uma auditoria
ao preparar o Lote 3 encontrou que o próprio `GetMeHandler` (`identity_access`, Lote 2) já importa
`modules.tenancy.infrastructure.persistence.repositories.sqlalchemy_tenant_repository` — um import
cross-module Application → Infrastructure real, nunca pego porque nenhum contrato `import-linter`
proibia isso. Regra corrigida para bater com o código, não o contrário (mesma disciplina de D103/
D196/D231): **leituras** cross-module (Application ou Infrastructure de um módulo lendo dados de
outro via seu Repository/model, nunca escrevendo) são aceitas quando o dado pertence
genuinamente a outro bounded context e não há alternativa sem duplicar a fonte de verdade — ex.:
`GetMeHandler` lendo `Tenant`; `SqlAlchemyDriverRepository.get_by_user_id` (`drivers`, Lote 3)
lendo `UserModel` (`identity_access`) para resolver `usuarios.motorista_id`. **Continua proibido**:
qualquer módulo **escrever** em tabelas de outro bounded context, e qualquer módulo importar
`interfaces/` (camada HTTP) de outro.

### Contratos que ainda NÃO existem — e por quê

Um contrato `layers` por bounded context (`interfaces → infrastructure → application → domain`,
dentro de cada `modules/<contexto>/`) seria o próximo passo natural — **não adicionado agora**
porque todo `modules/<contexto>/{domain,application,infrastructure,interfaces}/` está vazio (só
`__init__.py`). Um contrato contra código vazio passaria `KEPT` sem checar nada de verdade —
exatamente o tipo de "parece certo mas não prova nada" que este lote existe para evitar. Este
contrato entra junto com o primeiro código real de cada módulo, Sprint 11 Lote 2 em diante.

## Regras que dependem de disciplina humana, não de `import-linter` (ainda)

- **`application` nunca importa `infrastructure` do mesmo módulo diretamente** — depende da
  interface (`domain/repositories/`), recebe a implementação por injeção. `import-linter` não
  consegue expressar "a menos que seja injetado via construtor" — quando o primeiro
  `CommandHandler` real existir, isso vira parte do contrato `layers` por módulo mencionado acima.
- **`interfaces` nunca importa `domain` diretamente para lógica de negócio** — pode importar tipos
  de `domain` para anotação, nunca para *decidir* algo. Revisão de código continua necessária aqui.

## Como este documento cresce

Cada novo contrato `layers` por bounded context é adicionado ao `[tool.importlinter]` no mesmo
commit que cria o primeiro arquivo real daquele módulo — nunca depois, nunca como promessa.
