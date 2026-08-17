# 002 — Cadastros

Traduz para SQL as entidades de
[`../dictionary/001-cadastros.md`](../dictionary/001-cadastros.md) que compõem os Dados Mestres do
GestorFrete. As 8 regras de [`../README.md`](../README.md) (Lote 1) e o mapeamento de tipos de
[`README.md`](./README.md) já se aplicam a toda tabela abaixo.

## Gaps encontrados ao modelar (corrigidos na origem antes deste arquivo, D103)

Modelar fisicamente Cliente/Fornecedor/Filial/Motorista revelou três pontos em que o Data Dictionary
Funcional já aprovado precisava de ajuste — corrigidos em `docs/domain/001-cadastros.md` e
`docs/database/dictionary/001-cadastros.md` (e `006-financeiro.md`) **antes** deste arquivo, nunca
aqui diretamente (D103):

| Gap identificado | Decisão | Resultado |
|---|---|---|
| Cliente/Fornecedor/Filial só suportavam um endereço embutido (VO único) | **D182** | Nova entidade `Endereço`, referência polimórfica, suporta múltiplos endereços (matriz/cobrança/entrega) por entidade-dona |
| CNH era campo fixo em `Motorista` — não suportava RG, exame toxicológico, registro ANTT | **D183** | Nova entidade `Documento do Motorista` (1:N), `TIPO_DOCUMENTO` extensível |
| "Categoria Financeira" pedida nesta rodada duplicaria `Plano de Contas` (`006-financeiro.md`) | **D184** | `Plano de Contas` enriquecido com `TIPO` (Receita/Despesa) e `CATEGORIA_PAI_ID` (hierarquia) — nenhuma entidade nova |
| `usuarios.funcionario_id` (`001-core.md`) sempre referenciou `funcionarios(id)`, mas essa tabela nunca foi criada — `Funcionário` está no Domain Model e no Data Dictionary (`001-cadastros.md`) desde as fases anteriores, com atributos completos, e simplesmente não tinha DDL físico ainda. Achado ao montar `FOREIGN_KEYS.md`, mesma natureza de D194 (referência documentada sem `CREATE TABLE`) | **D196** | Tabela `funcionarios` criada abaixo, mesmo padrão de `motoristas` (vínculo a `Usuário` vive só do lado de `usuarios.funcionario_id`, sem coluna redundante aqui) |

## Escopo deste lote — o que fica para depois

Cobre exatamente o pedido: Cliente, Endereço, Contato do Cliente, Motorista, Documento do
Motorista, Fornecedor, Centro de Custo — mais `papeis`/`filiais` referenciadas (já modeladas em
`001-core.md`, não recriadas). **Fora do escopo, explicitamente adiado**:

- **Categoria de Veículo**: pertence a `003-frota.md` (Data Dictionary) — sua tabela física nasce em
  `relational/004-frota.md`, não aqui, para manter o mapeamento 1:1 entre lote relacional e
  categoria do dicionário.
- **Categoria Financeira**: não é uma tabela própria — reconciliada em `Plano de Contas` (D184,
  ver acima); sua tabela física (`plano_contas`) nasce em `relational/007-financeiro.md`.
- **Seguradora, Tabela de Preço, Item de Tabela de Preço, Rota Padrão, Trecho de Rota, Praça de
  Pedágio**: as 6 entidades restantes de `001-cadastros.md` não citadas no pedido desta rodada.
  **Atualização**: `Tabela de Preço`/`Item de Tabela de Preço` foram trazidas para
  `relational/003-operacao.md` (dependência de Cotação/Contrato de Frete) e `Seguradora` para
  `relational/004-frota.md` (dependência de Apólice de Seguro Veicular) — mesmo critério de
  "dependência real" aplicado nos dois casos. Restam apenas `Rota Padrão`, `Trecho de Rota` e
  `Praça de Pedágio`, ainda sem consumidor direto identificado.

---

## `enderecos`

Implementação física de `Endereço` (D182) — nasce primeiro porque `clientes`/`fornecedores`
referenciam este padrão por trás, embora a FK real seja no sentido oposto (endereço aponta para a
entidade-dona, não o contrário).

```sql
CREATE TYPE enderecos_entidade_tipo_enum AS ENUM ('CLIENTE', 'FORNECEDOR', 'FILIAL');
-- D231 — 'FILIAL' restaurado/confirmado: D182 sempre pretendeu que Filial usasse este padrão
-- polimórfico ("Cliente, Fornecedor e Filial podem ter múltiplos endereços"), mas a migração
-- nunca foi completada — `filiais.endereco` (001-core.md) continuou existindo como coluna JSONB
-- embutida, redundante com esta tabela. Corrigido agora: `filiais.endereco` removida (ver
-- 001-core.md). Achado ao preparar a API de Endereços (Sprint 10, Lote 3).
CREATE TYPE enderecos_tipo_endereco_enum AS ENUM ('PRINCIPAL', 'COBRANCA', 'ENTREGA', 'OUTRO');

CREATE TABLE enderecos (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    entidade_tipo   enderecos_entidade_tipo_enum NOT NULL,
    entidade_id     UUID NOT NULL,          -- sem FK física (polimórfico) — integridade garantida na aplicação
    tipo_endereco   enderecos_tipo_endereco_enum NOT NULL DEFAULT 'PRINCIPAL',
    logradouro      TEXT NOT NULL,
    numero          TEXT,
    complemento     TEXT,
    bairro          TEXT NOT NULL,
    cidade          TEXT NOT NULL,
    uf              TEXT NOT NULL,
    cep             TEXT NOT NULL,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    criado_por      UUID,
    atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_por  UUID,
    excluido_em     TIMESTAMPTZ,
    excluido_por    UUID
);

CREATE INDEX idx_enderecos_entidade_tipo_entidade_id
    ON enderecos (entidade_tipo, entidade_id) WHERE excluido_em IS NULL;

CREATE UNIQUE INDEX uq_enderecos_entidade_principal
    ON enderecos (entidade_tipo, entidade_id)
    WHERE tipo_endereco = 'PRINCIPAL' AND excluido_em IS NULL;
    -- no máximo um endereço Principal vigente por entidade-dona
```

Referência polimórfica sem FK de banco é uma exceção deliberada à regra geral — `entidade_id` pode
apontar para `clientes`, `fornecedores` ou `filiais` conforme `entidade_tipo`, e o PostgreSQL não
suporta FK condicional nativamente. Integridade garantida na camada de aplicação (mesmo padrão já
aceito para `logs_auditoria.entidade_id`, [`../AUDIT_MODEL.md`](../AUDIT_MODEL.md)).

## `clientes`

```sql
CREATE TABLE clientes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    codigo          TEXT NOT NULL,
    versao          INTEGER NOT NULL DEFAULT 1,
    razao_social    TEXT NOT NULL,
    nome_fantasia   TEXT,
    cnpj_cpf        TEXT NOT NULL,
    telefone        TEXT,
    email           TEXT,
    status          TEXT NOT NULL DEFAULT 'ATIVO',   -- Ativo/Inativo, soft-delete-like (ver dictionary)
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    criado_por      UUID,
    atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_por  UUID,
    excluido_em     TIMESTAMPTZ,
    excluido_por    UUID,

    CONSTRAINT uq_clientes_tenant_id_codigo UNIQUE (tenant_id, codigo),
    CONSTRAINT uq_clientes_tenant_id_cnpj_cpf UNIQUE (tenant_id, cnpj_cpf)
);

CREATE INDEX idx_clientes_tenant_id_cnpj_cpf ON clientes (tenant_id, cnpj_cpf) WHERE excluido_em IS NULL;
CREATE INDEX idx_clientes_tenant_id_nome ON clientes (tenant_id, razao_social) WHERE excluido_em IS NULL;
CREATE INDEX idx_clientes_tenant_id_status ON clientes (tenant_id, status) WHERE excluido_em IS NULL;
```

## `contatos_cliente`

```sql
CREATE TABLE contatos_cliente (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    cliente_id      UUID NOT NULL REFERENCES clientes(id),
    nome            TEXT NOT NULL,
    cargo           TEXT,
    telefone        TEXT,
    email           TEXT,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT now(),
    excluido_em     TIMESTAMPTZ
);

CREATE INDEX idx_contatos_cliente_cliente_id ON contatos_cliente (cliente_id) WHERE excluido_em IS NULL;
```

## `motoristas`

```sql
CREATE TYPE motoristas_tipo_vinculo_enum AS ENUM ('EMPREGADO', 'AUTONOMO');
CREATE TYPE motoristas_status_aptidao_enum AS ENUM ('APTO', 'BLOQUEADO');

CREATE TABLE motoristas (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    codigo          TEXT NOT NULL,
    versao          INTEGER NOT NULL DEFAULT 1,
    nome            TEXT NOT NULL,
    cpf             TEXT NOT NULL,
    telefone        TEXT,
    email           TEXT,
    tipo_vinculo    motoristas_tipo_vinculo_enum NOT NULL,
    status_aptidao  motoristas_status_aptidao_enum NOT NULL DEFAULT 'APTO',
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    criado_por      UUID,
    atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_por  UUID,
    excluido_em     TIMESTAMPTZ,
    excluido_por    UUID,

    CONSTRAINT uq_motoristas_tenant_id_codigo UNIQUE (tenant_id, codigo),
    CONSTRAINT uq_motoristas_tenant_id_cpf UNIQUE (tenant_id, cpf)
);

CREATE INDEX idx_motoristas_tenant_id_cpf ON motoristas (tenant_id, cpf) WHERE excluido_em IS NULL;
CREATE INDEX idx_motoristas_tenant_id_status_aptidao
    ON motoristas (tenant_id, status_aptidao) WHERE excluido_em IS NULL;
```

`status_aptidao` é **calculado**, não editável diretamente pela aplicação de formulário — recalculado
sempre que uma linha de `documentos_motorista` do tipo `CNH` muda (trigger ou lógica de aplicação, a
confirmar em `MIGRATIONS.md`/backend, não decidido aqui).

## `documentos_motorista`

Implementação física de `Documento do Motorista` (D183).

```sql
CREATE TYPE documentos_motorista_tipo_documento_enum AS ENUM
    ('CNH', 'RG', 'EXAME_TOXICOLOGICO', 'REGISTRO_ANTT');
CREATE TYPE documentos_motorista_categoria_cnh_enum AS ENUM ('A', 'B', 'C', 'D', 'E');
CREATE TYPE documentos_motorista_status_enum AS ENUM ('VALIDO', 'VENCIDO');

CREATE TABLE documentos_motorista (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    motorista_id    UUID NOT NULL REFERENCES motoristas(id),
    tipo_documento  documentos_motorista_tipo_documento_enum NOT NULL,
    numero          TEXT NOT NULL,
    categoria_cnh   documentos_motorista_categoria_cnh_enum,   -- só quando tipo_documento = CNH
    data_validade   DATE,
    arquivo_id      UUID,
    status          documentos_motorista_status_enum NOT NULL DEFAULT 'VALIDO',
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    criado_por      UUID,
    atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_por  UUID,

    CONSTRAINT ck_documentos_motorista_categoria_so_cnh
        CHECK (categoria_cnh IS NULL OR tipo_documento = 'CNH')
    -- "Documento do Motorista não pode existir sem Motorista": já garantido por
    -- motorista_id UUID NOT NULL REFERENCES motoristas(id) — não precisa de constraint adicional
);

CREATE INDEX idx_documentos_motorista_motorista_id ON documentos_motorista (motorista_id);
CREATE INDEX idx_documentos_motorista_data_validade
    ON documentos_motorista (data_validade) WHERE status = 'VALIDO';
```

## `funcionarios`

Implementação física de `Funcionário` (D196 — gap retroativo: `usuarios.funcionario_id`
já existia desde `001-core.md` sem que esta tabela tivesse sido criada).

```sql
CREATE TABLE funcionarios (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    codigo          TEXT NOT NULL,
    versao          INTEGER NOT NULL DEFAULT 1,
    nome            TEXT NOT NULL,
    cargo           TEXT NOT NULL,
    data_admissao   DATE,
    status          TEXT NOT NULL DEFAULT 'ATIVO',   -- Ativo/Inativo
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    criado_por      UUID,
    atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_por  UUID,
    excluido_em     TIMESTAMPTZ,
    excluido_por    UUID,

    CONSTRAINT uq_funcionarios_tenant_id_codigo UNIQUE (tenant_id, codigo)
);

CREATE INDEX idx_funcionarios_tenant_id_status ON funcionarios (tenant_id, status) WHERE excluido_em IS NULL;
```

Sem coluna `usuario_id` aqui — mesmo padrão já usado para `motoristas`: o vínculo opcional
Funcionário↔Usuário vive inteiramente do lado de `usuarios.funcionario_id`
(`ck_usuarios_motorista_xor_funcionario` já garante no máximo um dos dois preenchido por Usuário).
Uma segunda FK nesta tabela apontando de volta para `usuarios` seria uma segunda origem da verdade
para a mesma relação 1:1 — evitado de propósito.

## `fornecedores`

```sql
CREATE TYPE fornecedores_tipo_principal_enum AS ENUM
    ('PECA', 'RECAPAGEM', 'SEGURO', 'OFICINA', 'POSTO', 'BORRACHARIA', 'GUINCHO', 'OUTRO');

CREATE TABLE fornecedores (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    codigo          TEXT NOT NULL,
    versao          INTEGER NOT NULL DEFAULT 1,
    razao_social    TEXT NOT NULL,
    cnpj            TEXT NOT NULL,
    telefone        TEXT,
    tipo_principal  fornecedores_tipo_principal_enum,
    status          TEXT NOT NULL DEFAULT 'ATIVO',
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    criado_por      UUID,
    atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_por  UUID,
    excluido_em     TIMESTAMPTZ,
    excluido_por    UUID,

    CONSTRAINT uq_fornecedores_tenant_id_codigo UNIQUE (tenant_id, codigo),
    CONSTRAINT uq_fornecedores_tenant_id_cnpj UNIQUE (tenant_id, cnpj)
);

CREATE INDEX idx_fornecedores_tenant_id_cnpj ON fornecedores (tenant_id, cnpj) WHERE excluido_em IS NULL;
```

`fornecedores` é deliberadamente genérico — Oficina, Posto, Borracharia, Seguradora e Guincho são
todos a mesma tabela, diferenciados por `tipo_principal` (Enum), nunca tabelas separadas (D076 —
mesmo raciocínio já aplicado a `Evento de Rastreamento`/`Sugestão de IA`: especialização por
categoria, não por tabela).

## `centros_custo`

```sql
CREATE TABLE centros_custo (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id),
    codigo          TEXT NOT NULL,
    versao          INTEGER NOT NULL DEFAULT 1,
    codigo_contabil TEXT NOT NULL,
    nome            TEXT NOT NULL,
    filial_id       UUID REFERENCES filiais(id),
    status          TEXT NOT NULL DEFAULT 'ATIVO',
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    criado_por      UUID,
    atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_por  UUID,
    excluido_em     TIMESTAMPTZ,
    excluido_por    UUID,

    CONSTRAINT uq_centros_custo_tenant_id_codigo UNIQUE (tenant_id, codigo),
    CONSTRAINT uq_centros_custo_tenant_id_codigo_contabil UNIQUE (tenant_id, codigo_contabil)
);
```

`centros_custo` guarda **só identidade e classificação** — nenhuma coluna de saldo, indicador ou
valor acumulado (reforço direto de D090: qualquer "custo por centro de custo" é calculado por
`analytics` a partir de `contas_pagar`/rateios que o referenciam, nunca armazenado aqui).

## `papeis` e `filiais` — referenciadas, não recriadas

Já modeladas em [`001-core.md`](./001-core.md) (Lote 2). Toda tabela deste arquivo que precisa de
um `papel_id`/`filial_id` referencia `papeis(id)`/`filiais(id)` diretamente — nenhuma duplicação.

## DER textual deste lote

```
                              tenants
                                 │
        ┌────────────┬──────────┼──────────┬───────────────┐
        │            │          │          │               │
     clientes   fornecedores  motoristas  filiais      centros_custo
        │            │          │          │               │
        │ 1:N         │ 1:N      │ 1:N       │ 1:N            │ N:1
        ▼            ▼          ▼          ▼               ▼
  contatos_cliente  enderecos  documentos  enderecos    filial_id
                    (entidade_ _motorista  (entidade_
                     tipo=          tipo=
                    FORNECEDOR)    FILIAL)

  enderecos também aponta para clientes (entidade_tipo = CLIENTE) — arco omitido acima por espaço,
  mesma FK polimórfica para as três entidades-dona (D231 — `filiais.endereco` embutido, que existia
  desde `001-core.md`, foi removido; Filial passa a usar exclusivamente este padrão, completando o
  que D182 já pretendia).
```

## Constraints de integridade — resumo

| Regra de negócio | Constraint física |
|---|---|
| CPF único por tenant | `uq_motoristas_tenant_id_cpf` |
| CNPJ único por tenant (Cliente) | `uq_clientes_tenant_id_cnpj_cpf` |
| CNPJ único por tenant (Fornecedor) | `uq_fornecedores_tenant_id_cnpj` |
| Código funcional único por tenant | `uq_<tabela>_tenant_id_codigo` em toda tabela |
| Documento do Motorista não existe sem Motorista | `motorista_id UUID NOT NULL REFERENCES motoristas(id)` |
| Categoria CNH só faz sentido para `TIPO_DOCUMENTO = CNH` | `ck_documentos_motorista_categoria_so_cnh` |
| No máximo um endereço Principal vigente por entidade-dona | `uq_enderecos_entidade_principal` (índice único parcial) |

> **Nota sobre "categoria não pode ser pai dela mesma"**: essa constraint se aplica a
> `plano_contas.categoria_pai_id` (D184), não a nenhuma tabela deste lote — modelada em
> `relational/007-financeiro.md`, quando `plano_contas` for criada.

## Como este arquivo cresce

Concluído para o escopo deste lote. `Seguradora` e `Tabela de Preço`/`Item de Tabela de Preço` já
foram criadas em lotes seguintes por dependência real (ver nota acima). Restam `Rota Padrão`,
`Trecho de Rota` e `Praça de Pedágio` para um lote de complemento, se e quando forem referenciadas.
