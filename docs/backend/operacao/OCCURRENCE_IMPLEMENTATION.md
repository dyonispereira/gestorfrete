# OCCURRENCE_IMPLEMENTATION.md — Ocorrência

Sub-recurso de `Trip` (D232, `017-trip-occurrences.md`). Genérica por design (D076) — uma única
entidade/tabela, `tipo` (`ATRASO`/`AVARIA`/`PANE`/`SINISTRO`/`OUTRO`) cobre todo o espectro, nunca
uma API por tipo.

## Modelo

`Occurrence(BaseEntity[UUID])` — `viagem_id`, `tipo`, `descricao`, `gravidade`
(`BAIXA`/`MEDIA`/`ALTA`/`CRITICA`, opcional), `status` (`ABERTA`/`RESOLVIDA`), `data_hora`.

`location` (`latitude`/`longitude`) é aceito no `POST` mas **não persistido** — `ocorrencias` não
tem colunas físicas para isso (`relational/003-operacao.md` confirmado por leitura direta,
`017-trip-occurrences.md` já documenta essa lacuna conhecida). O schema aceita o campo, o handler o
ignora silenciosamente na escrita (nunca inventa uma coluna fora da DDL congelada) — mesma
disciplina de `TripSnapshots` rejeitando escrita em campo `readOnly`.

## Comandos

- `CreateOccurrenceHandler`: cria em `ABERTA`; publica `OcorrenciaRegistrada` sempre, e também
  `AvariaRegistrada` quando `tipo=AVARIA` (um único `POST` pode gerar dois eventos,
  `017-trip-occurrences.md`). **Não** move `Trip.status_operacional` para `INTERROMPIDA`
  automaticamente — são ações deliberadamente separadas (Gestor decide se a Ocorrência justifica
  `commands/interromper`).
- `UpdateOccurrenceHandler`: uso principal `status: RESOLVIDA`. Sem `DELETE` (RBAC só tem `.view`/
  `.create`/`.edit`, confirmado em `RBAC_MATRIX.md` §7.13).

## Erros

`FREIGHT_OCCURRENCE_NOT_FOUND` (404). Nenhum erro de negócio dedicado além disso — Ocorrência não
tem invariante de unicidade/estado complexo.

## Auditoria e tenant isolation

Mesmo padrão do projeto: `logs_auditoria` em toda criação/edição;
`SqlAlchemyOccurrenceRepository` filtra por `get_current_tenant_id()`.
