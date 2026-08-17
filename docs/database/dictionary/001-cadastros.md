# 001 — Cadastros (Dicionário de Dados Funcional)

Atributos distintivos das 16 entidades de [`../../domain/001-cadastros.md`](../../domain/001-cadastros.md).
Atributos universais (`ID`, `CODIGO`, `TENANT_ID`, `VERSAO`, `CRIADO_EM/POR`, `ATUALIZADO_EM/POR`,
`STATUS`) não são repetidos aqui (D069) — ver [`README.md`](./README.md), que também define os
Tipos Conceituais Padronizados usados na coluna abaixo.

> **Retrofit desta revisão**: a coluna Tipo Conceitual foi corrigida para usar exclusivamente o
> vocabulário padronizado (antes usava "Texto", "VO X", "UUID (referência)" ad-hoc) — ver
> [`README.md`](./README.md), Tipos Conceituais Padronizados.

---

## Cliente

Dono: `crm` · Natureza: Master Data (D036/D048)

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Pode Alterar | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|---|
| CLIENTE.RAZAO_SOCIAL | Razão Social | Texto Curto | Sim | Informado | `crm` | Sim | Interno | |
| CLIENTE.NOME_FANTASIA | Nome Fantasia | Texto Curto | Não | Informado | `crm` | Sim | Interno | |
| CLIENTE.CNPJ_CPF | CNPJ/CPF | Texto Curto | Sim | Informado | `crm` | Sim | LGPD (quando CPF), Confidencial | Value Object CNPJ/CPF (ver `shared/VALUE_OBJECTS.md`); único por tenant |
| CLIENTE.TELEFONE | Telefone | Texto Curto | Não | Informado | `crm` | Não | LGPD quando pessoa física | Value Object Telefone |
| CLIENTE.EMAIL | E-mail | Texto Curto | Não | Informado | `crm` | Não | LGPD quando pessoa física | Value Object E-mail |

> **D182**: `CLIENTE.ENDERECO` deixou de existir como atributo embutido — Cliente pode ter múltiplos
> endereços (matriz, cobrança, entrega). Ver entidade **Endereço**, ao final deste documento.

## Contato do Cliente

Dono: `crm` · Natureza: Master Data (parte do agregado Cliente)

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Pode Alterar | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|---|
| CONTATO_CLIENTE.CLIENTE_ID | Cliente | Referência | Sim | Capturado (sistema) | Ninguém | Não | Interno | FK para Cliente |
| CONTATO_CLIENTE.NOME | Nome | Texto Curto | Sim | Informado | `crm` | Não | LGPD | |
| CONTATO_CLIENTE.CARGO | Cargo | Texto Curto | Não | Informado | `crm` | Não | Interno | |
| CONTATO_CLIENTE.TELEFONE | Telefone | Texto Curto | Não | Informado | `crm` | Não | LGPD | Value Object Telefone |
| CONTATO_CLIENTE.EMAIL | E-mail | Texto Curto | Não | Informado | `crm` | Não | LGPD | Value Object E-mail; canal de notificação preferencial |

## Fornecedor

Dono: `maintenance` · Natureza: Master Data

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Pode Alterar | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|---|
| FORNECEDOR.RAZAO_SOCIAL | Razão Social | Texto Curto | Sim | Informado | `maintenance` | Sim | Interno | |
| FORNECEDOR.CNPJ | CNPJ | Texto Curto | Sim | Informado | `maintenance` | Sim | Interno | Value Object CNPJ; único por tenant |
| FORNECEDOR.TELEFONE | Telefone | Texto Curto | Não | Informado | `maintenance` | Não | Interno | Value Object Telefone |
| FORNECEDOR.TIPO_PRINCIPAL | Tipo de fornecimento principal | Enum | Não | Informado | `maintenance` | Não | Interno | Valores: Peça / Recapagem / Seguro / Outro. Informativo, não restringe o que pode ser cadastrado |

> **D182**: `FORNECEDOR.ENDERECO` idem Cliente — ver entidade **Endereço**, ao final deste documento.

## Motorista

Dono: `drivers` · Natureza: Master Data

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Pode Alterar | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|---|
| MOTORISTA.NOME | Nome | Texto Curto | Sim | Informado | `drivers` | Sim | LGPD | |
| MOTORISTA.CPF | CPF | Texto Curto | Sim | Informado | `drivers` | Sim | LGPD, Confidencial | Value Object CPF; único por tenant |
| MOTORISTA.TELEFONE | Telefone | Texto Curto | Não | Informado | `drivers` | Não | LGPD | Value Object Telefone |
| MOTORISTA.EMAIL | E-mail | Texto Curto | Não | Informado | `drivers` | Não | LGPD | Value Object E-mail |
| MOTORISTA.TIPO_VINCULO | Tipo de vínculo | Enum | Sim | Informado | `drivers` | Não | Interno | Valores: Empregado/Autônomo. Autônomo exige CIOT — ver [`../../flows/009-FISCAL.md`](../../flows/009-FISCAL.md) |
| MOTORISTA.STATUS_APTIDAO | Status de aptidão | Enum | Sim | Calculado (a partir da CNH vigente em `Documento do Motorista` e bloqueios manuais) | `drivers` | Sim | Interno, Crítico | Valores: Apto/Bloqueado. Invariante oficial: motorista `Bloqueado` não pode iniciar viagem |

> **D183**: `CNH_NUMERO`/`CNH_CATEGORIA`/`CNH_VALIDADE` deixaram de ser campos fixos — CNH agora é
> um `TIPO_DOCUMENTO` de **Documento do Motorista** (ao final deste documento), junto de RG, Exame
> Toxicológico e Registro ANTT.

## Funcionário

Dono: `identity_access` · Natureza: Master Data

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Pode Alterar | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|---|
| FUNCIONARIO.NOME | Nome | Texto Curto | Sim | Informado | `identity_access` | Sim | LGPD | |
| FUNCIONARIO.CARGO | Cargo | Texto Curto | Sim | Informado | `identity_access` | Sim | Interno | |
| FUNCIONARIO.DATA_ADMISSAO | Data de admissão | Data | Não | Informado | `identity_access` | Não | Interno | Granularidade: dia (D074) |
| FUNCIONARIO.USUARIO_ID | Usuário vinculado | Referência | Não | Capturado (sistema) | `identity_access` | Não | Interno | Opcional; no máximo um Usuário por Funcionário |

## Seguradora

Dono: `fleet` · Natureza: Master Data

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Pode Alterar | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|---|
| SEGURADORA.RAZAO_SOCIAL | Razão Social | Texto Curto | Sim | Informado | `fleet` | Não | Interno | |
| SEGURADORA.CNPJ | CNPJ | Texto Curto | Sim | Informado | `fleet` | Não | Interno | Value Object CNPJ; único por tenant |
| SEGURADORA.TELEFONE | Telefone | Texto Curto | Não | Informado | `fleet` | Não | Interno | Value Object Telefone |

## Filial

Dono: `tenancy` · Natureza: Master Data

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Pode Alterar | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|---|
| FILIAL.NOME | Nome | Texto Curto | Sim | Informado | `tenancy` | Sim | Interno | |
| FILIAL.EH_MATRIZ | É matriz? | Booleano | Sim | Informado | `tenancy` | Não | Interno | Exatamente uma Filial matriz por tenant |

> **D182**: `FILIAL.ENDERECO` idem Cliente/Fornecedor — ver entidade **Endereço**, ao final deste
> documento.

## Centro de Custo

Dono: `financial` · Natureza: Master Data

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Pode Alterar | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|---|
| CENTRO_CUSTO.CODIGO_CONTABIL | Código contábil | Texto Curto | Sim | Informado | `financial` | Não | Financeiro | Único por tenant |
| CENTRO_CUSTO.NOME | Nome | Texto Curto | Sim | Informado | `financial` | Sim | Interno | |
| CENTRO_CUSTO.FILIAL_ID | Filial vinculada | Referência | Não | Capturado (sistema) | `financial` | Não | Interno | Opcional |

## Tabela de Preço

Dono: `pricing` · Natureza: Master Data

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Pode Alterar | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|---|
| TABELA_PRECO.NOME | Nome | Texto Curto | Sim | Informado | `pricing` | Sim | Interno | |
| TABELA_PRECO.VIGENCIA_INICIO | Início da vigência | Data | Sim | Informado | `pricing` | Não | Interno | Granularidade: dia (D074) |
| TABELA_PRECO.VIGENCIA_FIM | Fim da vigência | Data | Não | Informado | `pricing` | Não | Interno | Granularidade: dia (D074) |
| TABELA_PRECO.CLIENTE_ID | Cliente específico | Referência | Não | Informado | `pricing` | Não | Interno | Opcional; ausente = tabela geral |
| TABELA_PRECO.STATUS | Status | Enum | Sim | Calculado (a partir da vigência e publicação) | `pricing` | Sim | Interno | Valores: Rascunho/Vigente/Expirada |

## Item de Tabela de Preço

Dono: `pricing` · Natureza: Master Data (parte do agregado Tabela de Preço)

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Pode Alterar | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|---|
| ITEM_TABELA_PRECO.TABELA_PRECO_ID | Tabela de Preço | Referência | Sim | Capturado (sistema) | Ninguém | Não | Interno | |
| ITEM_TABELA_PRECO.CONDICAO | Rota/tipo de carga/faixa de peso | Texto Curto | Sim | Informado | `pricing` | Não | Interno | |
| ITEM_TABELA_PRECO.VALOR | Valor | Monetário | Sim | Informado | `pricing` | Não | Financeiro | Moeda: BRL (D075); maior que zero |

## Usuário

Dono: `identity_access` · Natureza: Master Data

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Pode Alterar | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|---|
| USUARIO.NOME | Nome | Texto Curto | Sim | Informado | `identity_access` | Não | LGPD | |
| USUARIO.EMAIL | E-mail | Texto Curto | Sim | Informado | `identity_access` | Sim | LGPD | Value Object E-mail; único por tenant, usado para login |
| USUARIO.SENHA_HASH | Hash da senha | Texto Curto | Sim | Capturado (sistema) | `identity_access` | Não | Confidencial, Crítico | Nunca em texto claro em nenhuma camada — nota de segurança, não só de dado |
| USUARIO.STATUS | Status | Enum | Sim | Informado/Calculado | `identity_access` | Sim | Interno | Valores: Ativo/Inativo/Bloqueado |
| USUARIO.MOTORISTA_ID / FUNCIONARIO_ID | Pessoa vinculada | Referência | Não | Capturado (sistema) | `identity_access` | Não | Interno | Opcional, no máximo um dos dois preenchido |

## Papel

Dono: `identity_access` · Natureza: Master Data

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Pode Alterar | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|---|
| PAPEL.NOME | Nome | Texto Curto | Sim | Informado | `identity_access` | Sim | Interno | Único por tenant — ver [`../../product/RBAC_MATRIX.md`](../../product/RBAC_MATRIX.md) |
| PAPEL.DESCRICAO | Descrição | Texto Longo | Não | Informado | `identity_access` | Não | Interno | |

## Permissão

Dono: `identity_access` · Natureza: Seed Data (catálogo do sistema, D048 — não criado pelo cliente)

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Pode Alterar | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|---|
| PERMISSAO.CODIGO | Código | Texto Curto | Sim | Importado (catálogo do sistema, D057/D058) | Ninguém (imutável por versão) | Não | Interno | Formato `bounded_context.entidade.acao` — ver [`../../product/RBAC_MATRIX.md`](../../product/RBAC_MATRIX.md) |
| PERMISSAO.NOME | Nome | Texto Curto | Sim | Importado | Ninguém | Não | Interno | |
| PERMISSAO.MODULO | Módulo | Texto Curto | Sim | Importado | Ninguém | Não | Interno | |

## Rota Padrão

Dono: `routing` · Natureza: Master Data

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Pode Alterar | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|---|
| ROTA_PADRAO.NOME | Nome | Texto Curto | Sim | Informado | `routing` | Não | Interno | |
| ROTA_PADRAO.ORIGEM | Origem | Texto Curto | Sim | Informado | `routing` | Não | Interno | |
| ROTA_PADRAO.DESTINO | Destino | Texto Curto | Sim | Informado | `routing` | Não | Interno | |

## Trecho de Rota

Dono: `routing` · Natureza: Master Data (parte do agregado Rota Padrão)

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Pode Alterar | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|---|
| TRECHO_ROTA.ROTA_PADRAO_ID | Rota Padrão | Referência | Sim | Capturado (sistema) | Ninguém | Não | Interno | |
| TRECHO_ROTA.DISTANCIA_KM | Distância (km) | Decimal | Sim | Capturado (API de roteirização) ou Informado | `routing` | Não | Interno | Maior que zero |
| TRECHO_ROTA.TEMPO_ESTIMADO | Tempo estimado (minutos) | Inteiro | Não | Capturado (API de roteirização) | `routing` | Não | Interno | |

## Praça de Pedágio

Dono: `routing` · Natureza: Master Data

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Pode Alterar | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|---|
| PRACA_PEDAGIO.NOME | Nome | Texto Curto | Sim | Informado | `routing` | Não | Interno | |
| PRACA_PEDAGIO.LOCALIZACAO | Localização | Localização | Sim | Informado | `routing` | Não | Interno | Latitude/Longitude |
| PRACA_PEDAGIO.VALOR_REFERENCIA | Valor de referência | Monetário | Sim | Informado | `routing` | Sim | Financeiro | Moeda: BRL (D075); maior ou igual a zero; usado no Custo Previsto — ver [`../../flows/005-FINANCEIRO.md`](../../flows/005-FINANCEIRO.md) |

---

> **Duas entidades novas abaixo (D182/D183), identificadas ao modelar a camada relacional
> (`docs/database/relational/002-cadastros.md`).**

## Endereço

Dono: segue a entidade-dona (`crm`/`maintenance`/`tenancy`) · Natureza: Master Data (parte do
agregado da entidade-dona).

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Pode Alterar | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|---|
| ENDERECO.ENTIDADE_TIPO / ENTIDADE_ID | Entidade-dona | Referência (polimórfica) | Sim | Capturado (sistema) | Ninguém | Não | Interno | `Cliente`/`Fornecedor`/`Filial` |
| ENDERECO.TIPO_ENDERECO | Tipo | Enum | Sim | Informado | Dono da entidade-alvo | Não | Interno | Vocabulário extensível (D120-style): `Principal`/`Cobrança`/`Entrega`/`Outro` |
| ENDERECO.LOGRADOURO | Logradouro | Texto Curto | Sim | Informado | Dono da entidade-alvo | Não | Interno | |
| ENDERECO.NUMERO | Número | Texto Curto | Não | Informado | Dono da entidade-alvo | Não | Interno | |
| ENDERECO.COMPLEMENTO | Complemento | Texto Curto | Não | Informado | Dono da entidade-alvo | Não | Interno | |
| ENDERECO.BAIRRO | Bairro | Texto Curto | Sim | Informado | Dono da entidade-alvo | Não | Interno | |
| ENDERECO.CIDADE | Cidade | Texto Curto | Sim | Informado | Dono da entidade-alvo | Não | Interno | |
| ENDERECO.UF | UF | Texto Curto | Sim | Informado | Dono da entidade-alvo | Não | Interno | |
| ENDERECO.CEP | CEP | Texto Curto | Sim | Informado | Dono da entidade-alvo | Não | Interno | |

## Documento do Motorista

Dono: `drivers` · Natureza: Master Data (parte do agregado Motorista).

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Pode Alterar | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|---|
| DOCUMENTO_MOTORISTA.MOTORISTA_ID | Motorista | Referência | Sim | Capturado (sistema) | Ninguém | Não | Interno | FK |
| DOCUMENTO_MOTORISTA.TIPO_DOCUMENTO | Tipo | Enum | Sim | Informado | `drivers` | Não | Interno | Vocabulário extensível (D120-style): `CNH`/`RG`/`ExameToxicologico`/`RegistroANTT` |
| DOCUMENTO_MOTORISTA.NUMERO | Número | Texto Curto | Sim | Informado | `drivers` | Sim | LGPD, Confidencial | |
| DOCUMENTO_MOTORISTA.CATEGORIA | Categoria (quando CNH) | Enum | Não, obrigatório quando `TIPO_DOCUMENTO = CNH` | Informado | `drivers` | Sim | Interno | Valores: A/B/C/D/E |
| DOCUMENTO_MOTORISTA.DATA_VALIDADE | Validade | Data | Não | Informado | `drivers` | Sim | LGPD, Crítico | Granularidade: dia (D074). Quando `TIPO_DOCUMENTO = CNH`, gatilho de `MOTORISTA.STATUS_APTIDAO` |
| DOCUMENTO_MOTORISTA.ARQUIVO_ID | Documento digitalizado | Arquivo | Não | Informado | `drivers` | Não | Confidencial | D107 |
| DOCUMENTO_MOTORISTA.STATUS | Status | Enum | Sim | Calculado (a partir de `DATA_VALIDADE`) | `drivers` | Sim | Interno | Valores: `Válido`/`Vencido` |
