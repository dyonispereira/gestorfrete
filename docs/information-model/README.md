# docs/information-model — Índice do Modelo Informacional

Sprint 06. Esta pasta é a ponte entre o Modelo de Domínio ([`../domain/`](../domain/)) e o banco de
dados: ainda não é modelagem física (nenhuma tabela, nenhuma coluna de banco), mas já é sobre
**dados** — quem é dono de cada informação, o que é cadastro vs. transação vs. referência, como os
dados nascem e morrem, como são classificados e por quanto tempo são retidos.

## Estrutura

| # | Arquivo | Conteúdo | Status |
|---|---|---|---|
| 001 | [`DATA_OWNERSHIP.md`](./001-DATA_OWNERSHIP.md) | Quem é o dono de cada informação (D034/D040/D042) | Concluído |
| 002 | [`MASTER_DATA.md`](./002-MASTER_DATA.md) | Quais entidades são Master Data, governança e compartilhamento AgriHub | Concluído |
| 003 | [`TRANSACTIONAL_DATA.md`](./003-TRANSACTIONAL_DATA.md) | Entidades transacionais: frequência, crescimento, retenção, arquivamento | Concluído |
| 004 | [`REFERENCE_DATA.md`](./004-REFERENCE_DATA.md) | Cadastros auxiliares e Platform Reference Data (D046) | Concluído |
| 005 | [`DATA_LIFECYCLE.md`](./005-DATA_LIFECYCLE.md) | Como os dados nascem, evoluem e terminam; políticas de retenção | Concluído |
| 006 | [`DATA_CLASSIFICATION.md`](./006-DATA_CLASSIFICATION.md) | Classificação de todos os dados (Público, Confidencial, LGPD, etc.) | Concluído |
| 007 | [`DATA_RETENTION.md`](./007-DATA_RETENTION.md) | Por quanto tempo guardar cada tipo de informação | Concluído |
| — | [`HIGH_VOLUME_ENTITIES.md`](./HIGH_VOLUME_ENTITIES.md) | Classificação de volume (D049) e Time Series (D050) | Estrutura inicial, a expandir |

Sprint 06 concluído.

## Princípios do Modelo Informacional

Guia para qualquer documento novo desta pasta — na dúvida, a decisão que respeita estes princípios
vence:

1. Não duplicar informação.
2. Uma única fonte de verdade por informação (D042).
3. Todo dado possui dono (D040).
4. Dados derivados nunca são editáveis (D041).
5. Toda informação possui ciclo de vida (ver `005-DATA_LIFECYCLE.md`).
6. Toda informação possui classificação (ver `006-DATA_CLASSIFICATION.md`).
7. Toda informação crítica possui auditoria (D007).

## Conceitos-chave desta etapa (D046–D050)

- **Platform Reference Data** (D046) — dado sem `tenant_id`, compartilhado por todos os tenants,
  só a plataforma escreve (ex: País, Estado, Município).
- **Três níveis de posse** (D047) — Nível 1 Plataforma (sem tenant), Nível 2 Tenant (cadastros da
  empresa), Nível 3 Operação (dados vivos do dia a dia).
- **Seed Data × Master Data** (D048) — o que vem pronto com o sistema vs. o que o cliente cadastra.
- **Classificação de volume** (D049) e **Time Series** (D050) — ver
  [`HIGH_VOLUME_ENTITIES.md`](./HIGH_VOLUME_ENTITIES.md).

## Por que esta etapa existe

O objetivo é chegar à modelagem lógica do banco com o domínio, os fluxos, o *ownership*, a
classificação e o ciclo de vida dos dados já totalmente definidos — para que a modelagem de tabelas
seja quase mecânica, sem decisões estruturais em aberto (ver
[`../product/DECISIONS.md`](../product/DECISIONS.md), D035).

## Sequência após esta etapa

1. Concluir o Information Model (esta pasta).
2. `docs/product/RBAC_MATRIX.md` — matriz completa de permissões.
3. `docs/product/DATA_DICTIONARY_FUNCTIONAL.md` — dicionário funcional dos dados.
4. Modelo lógico do banco → 5. Modelo físico do banco → 6. OpenAPI → 7. Implementação.

## Ver também

- [`../domain/README.md`](../domain/README.md) — o Modelo de Domínio que esta pasta traduz para a
  linguagem de dados.
- [`../product/DECISIONS.md`](../product/DECISIONS.md) — todas as decisões arquiteturais e de
  produto, incluindo D040–D050 desta etapa.
