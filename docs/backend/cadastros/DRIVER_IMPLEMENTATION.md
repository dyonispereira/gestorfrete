# DRIVER_IMPLEMENTATION.md — `Motorista`, `Documento do Motorista` (`modules/drivers/`)

Contrato: [`../../api/009-drivers.md`](../../api/009-drivers.md). DDL:
[`../../database/relational/002-cadastros.md`](../../database/relational/002-cadastros.md)
(`motoristas`, `documentos_motorista`). RBAC: `drivers.driver.*` (`RBAC_MATRIX.md` §7.3).
Sem sub-recurso de Endereço — Motorista não está no `enderecos_entidade_tipo_enum`
(`009-drivers.md`, confirmado, nunca adicionado aqui como atalho).

## Domain

```
modules/drivers/domain/
├── value_objects/employment_type.py    # EMPREGADO / AUTONOMO (tipo_vinculo)
├── value_objects/fitness_status.py     # APTO / BLOQUEADO (status_aptidao)
├── value_objects/document_type.py      # CNH / RG / EXAME_TOXICOLOGICO / REGISTRO_ANTT
├── value_objects/cnh_category.py       # A / B / C / D / E
├── value_objects/document_status.py    # VALIDO / VENCIDO
├── entities/driver.py                  # Driver(BaseAggregateRoot[UUID])
├── entities/driver_document.py         # DriverDocument(BaseEntity[UUID])
└── repositories/
    ├── driver_repository.py            # + get_by_user_id (para /drivers/me)
    └── driver_document_repository.py
```

`Driver.create(codigo, nome, cpf, telefone, email, employment_type, audit)` — nasce sempre
`fitness_status=APTO` (D-alinhado à DDL, `status_aptidao NOT NULL DEFAULT 'APTO'`; nunca aceito no
`POST`, é `readOnly` no contrato). `Driver.block(blocked_by, now)` /
`Driver.unblock(unblocked_by, now)` — comandos nomeados (não um `PATCH` genérico de status,
`009-drivers.md`), cada um valida a transição (`DRIVERS_ALREADY_BLOCKED`/
`DRIVERS_ALREADY_UNBLOCKED` se já está no estado pedido).

**`fitness_status` é recalculado, não editável diretamente** — a regra oficial ("motorista
`Bloqueado` não pode iniciar viagem" é consumida por `freight`, fora de escopo aqui) desta camada é
mais simples: `fitness_status` só muda via `block()`/`unblock()` (ação manual, RBAC
`drivers.driver.block`/`.unblock`) **ou** — regra do Domain Model — quando o Documento do tipo CNH
vigente vence. Este lote implementa a via manual (`block`/`unblock`) e a leitura do `status`
calculado por `Documento do Motorista` (`DriverDocument.status`), mas **não** implementa um job/
trigger que automaticamente marca o Motorista como `BLOQUEADO` quando a CNH vence — isso é uma
regra assíncrona/agendada (fora do escopo de CRUD síncrono deste lote, mesma natureza de
`documentos_motorista_status`'s recálculo, que a DDL já anota como "trigger ou lógica de aplicação,
a confirmar em MIGRATIONS.md/backend, não decidido aqui"). Registrado como gap conhecido, não
inventado silenciosamente.

`DriverDocument.status` é **calculado na leitura** (`VALIDO` se `data_validade` é `None` ou futura,
`VENCIDO` caso contrário) — nunca uma coluna gravada e lida como fonte de verdade separada da
`data_validade`, evita os dois ficarem dessincronizados. `categoria_cnh` só aceito quando
`tipo_documento = CNH` (`ck_documentos_motorista_categoria_so_cnh` — validado no Domain antes de
bater na constraint física, erro de validação mais claro que um `IntegrityError` genérico).

## Infrastructure

`SqlAlchemyDriverRepository` — tenant-filtered, + `get_by_user_id(user_id)` (para
`GET /drivers/me`, resolve o Motorista a partir de `usuarios.motorista_id` do ator autenticado).
`SqlAlchemyDriverDocumentRepository` — tenant-filtered via `motorista_id` (que já é escopado por
tenant).

## Application

`CreateDriverCommand`/`UpdateDriverCommand`/`BlockDriverCommand`/`UnblockDriverCommand`/
`DeactivateDriverCommand` + `GetDriverQuery`/`ListDriversQuery`/`GetMyDriverQuery` (para
`/drivers/me`). `CreateDriverDocumentCommand`/`UpdateDriverDocumentCommand`/
`DeleteDriverDocumentCommand` + `ListDriverDocumentsQuery`. Auditoria (D344) em
create/block/unblock/deactivate — bloqueio/desbloqueio é auditoria crítica (criticidade Alta em
`RBAC_MATRIX.md`, aprovação de Gerente Operacional), sempre grava `logs_auditoria` mesmo sendo uma
mudança de um único campo.

`GetMyDriverQuery` resolve via `actor.user_id` → `SqlAlchemyDriverRepository.get_by_user_id` — se
não houver Motorista vinculado, `NotFoundError("DRIVERS_NOT_A_DRIVER_ACCOUNT")` (D-alinhado à nota
de `009-drivers.md`: "ex.: um Gestor Operacional chamando este endpoint por engano").

## Interfaces

`interfaces/api/driver_router.py` — `GET/POST /drivers`, `GET /drivers/me` (**antes** de
`GET /drivers/{id}` no registro de rotas do FastAPI — caso contrário `/drivers/me` seria capturado
pelo path param `{id}` e o FastAPI tentaria interpretar `"me"` como um `UUID`, erro de validação
400 em vez do endpoint correto; ordem de declaração importa em FastAPI para paths literais vs.
parametrizados que colidem), `PATCH /drivers/{id}`, `POST /drivers/{id}/block`,
`POST /drivers/{id}/unblock`, `DELETE /drivers/{id}`,
`GET/POST /drivers/{id}/documents`, `GET/PATCH/DELETE /drivers/{id}/documents/{documentId}`.

`GET /drivers/me` usa `drivers.driver.view_own` (Escopo "Próprio usuário", D053) — permissão
diferente de `drivers.driver.view`, checada separadamente (não é "a mesma view com id implícito", é
uma permissão própria que um Motorista tem mesmo sem `drivers.driver.view` geral).

## Erros

| Código | HTTP | Quando |
|---|---|---|
| `DRIVERS_DRIVER_NOT_FOUND` | 404 | Motorista não existe (ou outro tenant) |
| `DRIVERS_NOT_A_DRIVER_ACCOUNT` | 404 | `GET /drivers/me` sem `usuarios.motorista_id` |
| `DRIVERS_CPF_ALREADY_EXISTS` | 409 | `uq_motoristas_tenant_id_cpf` |
| `DRIVERS_ALREADY_BLOCKED` / `DRIVERS_ALREADY_UNBLOCKED` | 422 | Transição inválida de `block`/`unblock` |

`DRIVERS_DRIVER_HAS_ACTIVE_TRIP` (422, `DELETE`) **não implementado neste lote** — depende de
`alocacoes_recurso_viagem`/`freight` (Lote 4+), mesmo raciocínio de `CRM_CLIENT_HAS_ACTIVE_TRIPS`.

## Testes (D352)

- Unit: `Driver.create()`/`.block()`/`.unblock()` (transições inválidas), `DriverDocument.status`
  calculado, `categoria_cnh` só aceito para `CNH`.
- Integration: `SqlAlchemyDriverRepository`/`SqlAlchemyDriverDocumentRepository` contra Postgres
  real — tenant isolation, `get_by_user_id`, unicidade de CPF.
- E2E: `POST /drivers` → `GET` → `POST /block` (`fitness_status` muda) → `POST /unblock` →
  `POST /documents` (CNH) → `GET /drivers/me` (com um `usuarios.motorista_id` de teste) →
  `DELETE` via HTTP real.
- Auditoria: `POST`/`block`/`unblock`/`DELETE` geram `logs_auditoria`.
