# 056 — Driver Checklists

Bounded context proprietário: `maintenance` (Checklist, RBAC §7.11) — não `mobile`. **Documento sem
endpoints** (D305).

## D305 — Domain/Flow completos, DDL nunca traduzida

Auditoria desta preparação (D200 aplicado à API) encontrou algo diferente do presumido no kickoff:
`flows/007-CHECKLIST.md` **está**, de fato, plenamente especificado — 5 estados
(`PENDENTE`/`EM_PREENCHIMENTO`/`CONCLUIDO`/`APROVADO`/`REPROVADO`), transições, eventos
(`ChecklistIniciado`/`ChecklistConcluido`/`ChecklistAprovado`/`ChecklistReprovado`, este último já
em `EVENT_MAP.md`), e RBAC (`maintenance.checklist.view`/`.fill`/`.approve`/`.reject`/`.attach`/
`.view_history`, com `.fill`/`.attach` já marcados `●` App). **Nenhuma tabela física existe** para
Checklist/Item de Checklist/Modelo de Checklist em nenhum arquivo `relational/`.

Diferente da maioria dos gaps já corrigidos nesta sprint (tradução mecânica de `CREATE TABLE`
faltante, ex.: D196/D222/D269) — aqui a estrutura de **Modelo de Checklist** (quais itens compõem
cada tipo, qual item é crítico, qual o tipo de resposta esperada) nunca foi detalhada em nível de
Domain/Dictionary. `007-CHECKLIST.md` menciona "modelo de checklist (lista de itens a verificar)"
como pré-condição, sem especificar sua forma. Completar a DDL agora exigiria decidir essa estrutura
— **inventaria escopo novo, não corrigiria uma tradução pendente** (mesmo critério de restrição já
aplicado em D206, Sprint 09, para País/Estado/Município).

## Por que este documento não tem endpoints

D101/D102 — Domain/Dictionary/DDL são upstream da API. Sem tabela física, não há o que a API possa
consultar ou escrever de verdade; documentar endpoints "de mentira" (apontando para uma tabela que
não existe) seria pior do que não documentar nada.

## O que já existe, pronto para quando a DDL for escrita

- **Máquina de estados**: `flows/007-CHECKLIST.md`, cinco estados, transições e regras normativas
  já completas — a API futura pode seguir literalmente a mesma tabela usada em `018-trip-status.md`/
  `026-maintenance-orders.md` (comando por transição, nunca `PATCH status`).
- **RBAC**: já existe e já está corretamente marcado para o App (`maintenance.checklist.fill`/
  `.attach`, ● na coluna App) — nenhum código novo será necessário para o caso comum de
  preenchimento pelo Motorista.
- **Evento**: `ChecklistReprovado` já catalogado; `ChecklistIniciado`/`ChecklistConcluido`/
  `ChecklistAprovado` estão especificados no fluxo mas ainda não em `EVENT_MAP.md` — mesma família
  de gap já vista várias vezes nesta sprint (D239/D259/D270), a confirmar quando este módulo for
  formalizado.
- **Assinatura**: `assinaturas_digitais_documento_tipo_enum` já reserva `CHECKLIST` como valor
  futuro extensível (comentário na DDL, `relational/009-app_motorista.md`) — nenhuma migração de
  schema será necessária além do `ALTER TYPE`.

## Fora de escopo, não esquecido

Todo o módulo Checklist — cadastro de Modelo, preenchimento de item, aprovação/reprovação,
histórico — fica reservado para quando a estrutura de Modelo de Checklist for decidida em
Domain/Dictionary primeiro (D101), fora do escopo de um lote de API.

## Como este documento cresce

Quando `checklists`/`itens_checklist`/`modelos_checklist` (nomes ilustrativos, a decidir) existirem
fisicamente, este arquivo deixa de ser documentação-only e ganha os endpoints reais — a máquina de
estados e o RBAC já mapeados acima não precisam ser redecididos, só traduzidos.
