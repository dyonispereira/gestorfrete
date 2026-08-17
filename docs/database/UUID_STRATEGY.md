# UUID_STRATEGY.md — Estratégia de Identificadores

Implementação física de D029/D030 (dupla identidade — UUID técnico nunca exibido + código
funcional legível, configurável por tenant — decisão da fase de Modelo de Domínio) e D175.

## Dois identificadores, dois propósitos, nunca confundidos

| | ID Técnico | Código Funcional |
|---|---|---|
| Coluna física | `id UUID PRIMARY KEY` | `codigo TEXT NOT NULL` |
| Gerado por | Banco/aplicação, UUID v4 aleatório | Sequência configurável por tenant (`Configuração de Numeração`, [`dictionary/010-administracao.md`](./dictionary/010-administracao.md)) |
| Exibido ao usuário? | **Nunca** (D029) | Sempre — é o que aparece na tela |
| Usado em FK entre tabelas? | Sempre | Nunca |
| Muda de formato ao longo do tempo? | Nunca | Pode, se o tenant reconfigurar o formato (D030) — mas o histórico de códigos já emitidos nunca muda retroativamente |
| Exemplo | `8c9f8f6a-7a6d-4d8b-b9f0-22d8c5e6a1f0` | `MOT-000123`, `VEI-000045`, `VIA-2026-000001` |

```sql
CREATE TABLE motoristas (
    id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo   TEXT NOT NULL,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    -- ...
    CONSTRAINT uq_motoristas_tenant_id_codigo UNIQUE (tenant_id, codigo)
);
```

## Por que UUID e não `BIGSERIAL`

- **Multi-tenant desde o dia um** (D005): um `id` sequencial global vazaria informação entre tenants
  (ex: "tenant novo, poucos registros" ficaria visível pela magnitude do número) e complicaria
  qualquer futura necessidade de mover dados entre ambientes/réplicas.
- **Geração distribuída**: o app pode gerar o UUID antes mesmo de persistir (útil para idempotência,
  D111, e para o app Motorista offline gerar IDs localmente antes de sincronizar, D039).
- **Nunca exibido (D029)**, então o argumento de "UUID é feio para o usuário ver" nunca se aplica —
  só o `codigo` aparece em tela.

## Numeração do código funcional

Cada tipo de entidade tem sua própria sequência, controlada por
`Configuração de Numeração` (por entidade transacional comum) ou `Configuração Fiscal do Tenant`
(exclusiva para CT-e/MDF-e, D110 — nunca a mesma sequência) — ambas já modeladas no Data Dictionary
Funcional. Fisicamente, isso é uma tabela de contador por `(tenant_id, tipo_entidade)`, nunca uma
sequência `SERIAL` do PostgreSQL compartilhada entre tenants (que vazaria volume entre eles, mesmo
argumento da seção anterior) e nunca calculada como `MAX(codigo) + 1` (condição de corrida sob
concorrência) — o próximo número é obtido de forma atômica (`SELECT ... FOR UPDATE` ou sequência
dedicada por tenant/tipo, decisão de implementação a confirmar no Modelo Relacional de
Administração).

## Formato do código por tipo de entidade

O formato exato (prefixo, quantidade de dígitos, presença de ano) é configurável por tenant
(D030) — os exemplos abaixo são o padrão de fábrica, não uma regra fixa:

| Entidade | Formato padrão |
|---|---|
| Motorista | `MOT-000123` |
| Veículo Tracionador | `VEI-000045` |
| Viagem | `VIA-2026-000001` (inclui ano — alto volume, reinicia contagem anual) |
| CT-e | Segue numeração fiscal oficial (D110), não este padrão — regulada pela SEFAZ |

## Como este documento cresce

Regra estável. Detalhe de implementação do contador atômico (tabela de sequência vs. função de
banco) é decidido no Modelo Relacional de Administração, quando `Configuração de Numeração` virar
tabela física.
