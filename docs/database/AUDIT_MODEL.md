# AUDIT_MODEL.md — Modelo Físico de Auditoria

Implementação física de D007 (auditoria obrigatória, decisão de fundação do projeto) e D176, e da
entidade `Log de Auditoria` já modelada em
[`../database/dictionary/010-administracao.md`](./dictionary/010-administracao.md) (com sua tabela
de governança Quem/Quando/Origem/Antes/Depois/Motivo/Correlação/Rastreabilidade).

## Duas camadas de auditoria, nunca confundidas

| Camada | Onde vive | O que registra |
|---|---|---|
| **Auditoria leve** (toda tabela) | Colunas `criado_em`/`criado_por`/`atualizado_em`/`atualizado_por` na própria tabela | Quem criou/alterou pela última vez e quando — suficiente para a maioria das consultas do dia a dia |
| **Auditoria completa** (ações sensíveis) | Tabela física `logs_auditoria` | Histórico completo de cada ação sensível — múltiplas alterações da mesma linha, valores antes/depois, origem, motivo, correlação |

Não são redundantes: `atualizado_por`/`atualizado_em` respondem "quem mexeu por último", `logs_auditoria`
responde "o que exatamente mudou, em cada uma das vezes, e por quê".

## Colunas de auditoria leve (toda tabela principal)

```sql
criado_em    TIMESTAMPTZ NOT NULL DEFAULT now(),
criado_por    UUID NOT NULL REFERENCES usuarios(id),
atualizado_em    TIMESTAMPTZ NOT NULL DEFAULT now(),
atualizado_por    UUID NOT NULL REFERENCES usuarios(id)
```

`criado_por`/`atualizado_por` referenciam `usuarios(id)` sem `ON DELETE CASCADE` — um Usuário nunca é
excluído fisicamente (D001), então a referência permanece válida para sempre; ainda assim, ver a
nota de D147 abaixo para o caso de `logs_auditoria`, que vai além disso.

## Tabela `logs_auditoria` (implementação física de `Log de Auditoria`)

```sql
CREATE TABLE logs_auditoria (
    id                UUID PRIMARY KEY,
    entidade_tipo     TEXT NOT NULL,
    entidade_id       UUID NOT NULL,
    acao              logs_auditoria_acao_enum NOT NULL,
    ator_id           UUID,                    -- nulo quando ACAO = 'Sistema'
    ator_nome_snapshot TEXT NOT NULL,           -- D147 — nunca depende do Usuário ainda existir
    origem            logs_auditoria_origem_enum NOT NULL,
    dados_antes       JSONB,
    dados_depois      JSONB,
    motivo            TEXT,
    id_correlacao     UUID NOT NULL,
    data_hora         TIMESTAMPTZ NOT NULL DEFAULT now()
    -- sem atualizado_em/atualizado_por: logs_auditoria nunca é atualizada (D001/D037/D109)
    -- sem excluido_em/excluido_por: logs_auditoria nunca é excluída, nem logicamente
);
```

Pontos que traduzem decisões já tomadas no Data Dictionary Funcional para SQL concreto:

- **`ator_nome_snapshot`** existe fisicamente por causa de D147 — mesmo que a linha em `usuarios`
  seja removida (soft delete) ou o `ator_id` fique órfão por qualquer motivo, o log preserva
  significado.
- **Sem `ON DELETE CASCADE` em `ator_id`**: intencional — se um dia uma FK for necessária por
  integridade referencial, o comportamento correto é `ON DELETE SET NULL`, nunca `CASCADE` (apagar
  o log junto seria uma violação direta de D109).
- **Nenhuma coluna de soft delete nesta tabela**: `logs_auditoria` não tem `excluido_em`/`excluido_por`
  porque nem soft delete se aplica a ela — não existe cenário em que uma linha de auditoria "sai de
  circulação" (D109, reforço máximo).
- **`id_correlacao`** agrupa múltiplos logs de uma mesma transação de negócio (ex: uma transição de
  Viagem que dispara efeitos em `freight`, `financial` e `documents` simultaneamente) — sempre
  presente, nunca nulo.

## Particionamento

`logs_auditoria` é classificada como volume "Muito Alto"
([`../information-model/HIGH_VOLUME_ENTITIES.md`](../information-model/HIGH_VOLUME_ENTITIES.md)) —
particionada por `tenant_id` + `data_hora` desde a primeira migration (D179), mesma estratégia de
`posicoes_veiculo`. Detalhe de particionamento físico exato fica no Modelo Relacional de
Administração (`relational/`, categoria correspondente), não aqui.

## O que dispara um registro em `logs_auditoria`

Não é a aplicação decidindo caso a caso — é a mesma lista de "Auditoria" já declarada em cada
entidade do Data Dictionary Funcional desde `001-cadastros.md` (a coluna "Auditoria: D007" presente
em toda entidade). Nenhuma regra nova é criada aqui; este documento só formaliza onde esse já-
declarado destino físico vive.

## Como este documento cresce

Estável — a estrutura de `logs_auditoria` não muda por categoria. O que cresce é o vocabulário de
`logs_auditoria_acao_enum`/`logs_auditoria_origem_enum` (D120-style, extensível), conforme novas ações
sensíveis forem identificadas durante o Modelo Relacional.
