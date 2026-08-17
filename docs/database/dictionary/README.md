# docs/database/dictionary — Índice do Dicionário de Dados Funcional

Sprint 08. Este é o dicionário oficial de dados do GestorFrete: para cada atributo de cada
entidade, o que ele significa, de onde vem, quem é dono, se tem histórico, se é sensível — a
tradução do negócio para os dados (D063–D068), **não** o DER e **não** SQL. Modelagem física vem
depois, derivada daqui, não o contrário.

`docs/product/DATA_DICTIONARY_FUNCTIONAL.md` é apenas um ponteiro para esta pasta — todo o
conteúdo real vive aqui, organizado por categoria (mesma lógica de
[`../../domain/README.md`](../../domain/README.md)).

## Estrutura

| # | Arquivo | Categoria | Status |
|---|---|---|---|
| 001 | [`001-cadastros.md`](./001-cadastros.md) | Cadastros | Concluído |
| 002 | [`002-operacao.md`](./002-operacao.md) | Operação (Viagem e correlatas) | Concluído |
| 003 | [`003-frota.md`](./003-frota.md) | Frota | Concluído |
| 004 | [`004-manutencao.md`](./004-manutencao.md) | Manutenção | Concluído |
| 005 | [`005-pneus.md`](./005-pneus.md) | Pneus | Concluído |
| 006 | [`006-financeiro.md`](./006-financeiro.md) | Financeiro | Concluído |
| 007 | [`007-fiscal.md`](./007-fiscal.md) | Fiscal | Concluído |
| 008 | [`008-rastreamento.md`](./008-rastreamento.md) | Rastreamento | Concluído |
| 009 | [`009-app_motorista.md`](./009-app_motorista.md) | App Motorista | Concluído |
| 010 | [`010-administracao.md`](./010-administracao.md) | Administração da Plataforma | Concluído |
| 011 | [`011-bi.md`](./011-bi.md) | BI | Concluído |
| 012 | [`012-ia.md`](./012-ia.md) | IA | Concluído |

**Data Dictionary Funcional completo** — as 12 categorias planejadas estão com `Status: Concluído`.
Próxima etapa do roadmap: Modelo Lógico do Banco de Dados (ver
[`../../product/DECISIONS.md`](../../product/DECISIONS.md), D101).

## Convenções Globais (D069): atributos universais, não repetidos em cada arquivo

Todo atributo abaixo existe em **toda** entidade Nível 2/3 (D047), com o mesmo comportamento —
listá-los entidade por entidade seria repetição sem valor (D067: "por que este campo existe?" já
está respondido de forma idêntica todas as vezes). Cada arquivo de categoria lista apenas os
atributos **distintivos** de cada entidade; toda entidade **herda** os universais por convenção
(D069), nunca por cópia de documentação.

| Atributo | Descrição | Tipo Conceitual | Origem | Pode Alterar | Histórico | Observações |
|---|---|---|---|---|---|---|
| `<ENTIDADE>.ID` | UUID técnico | UUID (conceitual) | Capturado (sistema) | Ninguém (imutável) | Não | Nunca exibido ao usuário — D029 |
| `<ENTIDADE>.CODIGO` | Código funcional legível | Texto Curto | Capturado (sistema) | Ninguém (imutável) | Não | Formato configurável por tenant — D029/D030 |
| `<ENTIDADE>.TENANT_ID` | Tenant a que pertence | Referência | Capturado (sistema) | Ninguém (imutável) | Não | **Ausente** em Platform Reference Data — D046 |
| `<ENTIDADE>.VERSAO` | Contador de versão do registro | Inteiro | Calculado (sistema) | Ninguém diretamente | Não (é o próprio contador) | Suporte a controle de concorrência; incrementa a cada alteração |
| `<ENTIDADE>.CRIADO_EM` / `CRIADO_POR` | Quando e por quem foi criado | Data/Hora · Referência | Capturado (sistema) | Ninguém | Não (é o próprio registro de criação) | Auditoria padrão — D007; granularidade: segundo (D074) |
| `<ENTIDADE>.ATUALIZADO_EM` / `ATUALIZADO_POR` | Quando e por quem foi alterado pela última vez | Data/Hora · Referência | Capturado (sistema) | Ninguém diretamente | Sim, quando a entidade tem `StatusHistory` (D017/D018); senão, só o último valor | Granularidade: segundo (D074) |
| `<ENTIDADE>.STATUS` | Ativo/Inativo (entidades simples) ou o(s) campo(s) de status específico(s) (entidades com máquina de estados própria) | Enum | Ver máquina de estados da entidade | Varia | Ver D017/D018 | Soft delete nunca exclui fisicamente — D001. **Status compostos (ex: `ENCERRADA`) nunca são um destes campos — são sempre calculados, nunca persistidos (D072).** |

Todos os atributos universais acima são: **Auditáveis** (Sim, sempre — D007), **Não LGPD/Não
Sensíveis** (por padrão — exceto quando o próprio ID/Código carregar informação pessoal, o que não
ocorre no GestorFrete) e **Classificação: Interno** (por padrão). Nenhum metadado já definido em
[`../../information-model/`](../../information-model/), [`../../domain/`](../../domain/) ou
[`../../product/RBAC_MATRIX.md`](../../product/RBAC_MATRIX.md) é redefinido aqui (D070).

## Tipos Conceituais Padronizados

Vocabulário fechado — nunca usar variações como "String", "Varchar" ou "Char" na coluna Tipo
Conceitual; o dicionário funcional é independente de tecnologia (D068).

| Tipo | Uso |
|---|---|
| Texto Curto | Nomes, códigos, identificadores textuais — até ~255 caracteres |
| Texto Longo | Descrições, observações, conteúdo livre extenso |
| Inteiro | Contagens, quantidades sem fração |
| Decimal | Medidas com fração (distância, peso, litros) |
| Percentual | Valores expressos em % |
| Monetário | Sempre acompanhado de moeda associada (D075 — hoje sempre BRL) |
| Data | Apenas data, sem hora — granularidade dia (D074) |
| Data/Hora | Data com hora — granularidade padrão segundo, salvo indicação em contrário (D074) |
| Booleano | Verdadeiro/Falso |
| Enum | Conjunto fechado de valores nomeados |
| UUID (conceitual) | Identificador técnico único — nunca exibido ao usuário (D029) |
| Referência | Ponteiro para outra entidade (chave estrangeira conceitual) |
| Arquivo | Anexo genérico (D024) |
| Imagem | Anexo especificamente fotográfico |
| Localização | Coordenada geográfica (latitude/longitude) |
| Time Series | Série temporal de alto volume (D049/D050) |
| JSON Estruturado | Valor composto/aninhado sem entidade própria (ex: Endereço como Value Object) |

## Legenda das colunas usadas nas tabelas de cada categoria

| Coluna | Significado |
|---|---|
| Atributo | Identificador funcional `ENTIDADE.ATRIBUTO` (D063) |
| Nome | Nome de negócio, em português — nunca o nome técnico de banco (D068) |
| Tipo Conceitual | Um dos Tipos Conceituais Padronizados definidos acima — nunca um tipo físico de banco |
| Obrigatório | Sim/Não |
| Origem | Informado / Capturado / Calculado / Derivado / Importado (D043) |
| Pode Alterar | Qual bounded context pode escrever este atributo (D034/D064) |
| Histórico | Sim (append-only, D017/D018/D037) / Não |
| Classificação | Rótulos de [`../../information-model/006-DATA_CLASSIFICATION.md`](../../information-model/006-DATA_CLASSIFICATION.md) — Público/Interno/Confidencial/LGPD/Sensível/Crítico/Financeiro/Fiscal, quando não-Interno |
| Observações | Snapshot, cálculo, unicidade, Fonte Canônica (D035/D065) quando o atributo depende de um documento específico, e qualquer outra nota relevante |

Campos do template original que não viram coluna própria por serem redundantes com as acima:
**Natureza** (Master Data/Seed Data — já é uma propriedade da entidade inteira, não do atributo,
ver [`../../information-model/002-MASTER_DATA.md`](../../information-model/002-MASTER_DATA.md) e
`004-REFERENCE_DATA.md`, declarada uma vez no cabeçalho de cada entidade, não por atributo);
**Dono** (idem — uma entidade tem um dono, D033; "Pode Alterar" cobre a granularidade real que
varia por atributo, D064); **Auditável** (sempre Sim, D007 — não varia por atributo);
**Calculado?** (redundante com Origem = Calculado); **Valor padrão** (citado em Observações apenas
quando não-óbvio); **Relacionado com** (citado em Observações quando relevante, evitando uma coluna
majoritariamente vazia).

## Padrões de atributo

Quatro padrões recorrentes de comportamento de atributo — reconhecer qual se aplica evita
descrever cada campo do zero e mantém o vocabulário consistente entre arquivos.

**Snapshot** — ex: `VIAGEM.CLIENTE_SNAPSHOT`. Sempre: nunca sincroniza com a entidade de origem
(D073); registra o momento exato da captura (D071); preserva o histórico mesmo que o cadastro vivo
mude depois (D038).

**Referência** — ex: `VIAGEM.CLIENTE_ID`. Sempre: aponta para a entidade viva (não uma cópia);
acompanha qualquer alteração feita na entidade referenciada — é exatamente o oposto do Snapshot, e
os dois nunca devem ser confundidos no mesmo atributo.

**Calculado** — ex: `VIAGEM.MARGEM`. Nunca editável diretamente; obtido a partir de outros
atributos, em tempo real ou persistido apenas com justificativa (D066).

**Derivado** — ex: `DISPONIBILIDADE_VEICULO.STATUS`. Obtido a partir de sinais de **outras**
entidades/bounded contexts (via evento, D032), não apenas de atributos da própria entidade — a
diferença para Calculado é a origem cruzar fronteira de agregado/contexto.

**Estado Atual** (D081) — qualquer campo nomeado "Atual" (ex: `MOTORISTA_ATUAL_ID`,
`IMPLEMENTO_ATUAL_ID`, `LOCALIZACAO_ATUAL`) é sempre uma projeção de leitura rápida, nunca a fonte
da verdade — que continua sendo o histórico append-only correspondente (D037/D038/D079). É um caso
específico e nomeado do padrão Derivado acima.

**Time Series** — ex: `POSICAO_VEICULO.LATITUDE`. Sempre informa granularidade temporal (D074) e é
tratado como alto volume (D049/D050).

## Atributos Críticos (D077)

Alguns atributos recebem documentação complementar de governança — uma tabela dedicada
respondendo **Quem altera? / Quando muda? / Quem pode visualizar? / Quem nunca altera?** — além da
linha padrão na tabela de atributos. Não é obrigatório para todo atributo, apenas para os
classificados como Críticos: tipicamente status de máquina de estados (`STATUS_OPERACIONAL`,
`STATUS_FINANCEIRO`, `STATUS_FISCAL`), identificadores legais (`PLACA`, `CNPJ`, `CPF`), e valores
financeiros/operacionais sensíveis (`RECEITA_PREVISTA`, `RECEITA_REALIZADA`, `KM_INICIAL`,
`KM_FINAL`, `VALOR_FRETE`). Ver exemplo completo em
[`002-operacao.md`](./002-operacao.md#governança-dos-atributos-críticos--quatro-perguntas).

## Indicadores nunca são atributos operacionais (D090)

MTBF, MTTR, Disponibilidade, Confiabilidade, vida útil média, taxa de sucata prematura e
indicadores equivalentes **nunca** aparecem como um `Atributo` numa tabela de entidade deste
dicionário — são calculados por `analytics`/BI a partir dos dados brutos que o domínio operacional
de fato possui (histórico de status, custos, leituras). Se um arquivo de categoria menciona um
indicador, é apenas para explicar de onde os dados de origem vêm — nunca para declarar um campo
`ENTIDADE.INDICADOR_X` a ser persistido.

## Atenção especial: derivados, snapshot e time series

Três tipos de atributo exigem leitura cuidadosa da coluna Origem/Observações, não apenas do nome:

- **Derivado/Calculado** (ex: `VIAGEM.MEDIA_COMBUSTIVEL`): Origem = Calculado; nunca aceita
  digitação; só é persistido com justificativa (D066) — caso contrário, calculado em tempo real.
- **Snapshot** (ex: `VIAGEM.NOME_MOTORISTA_SNAPSHOT`): Origem = Capturado, mas capturado **uma
  única vez**, em um momento explícito e nomeado (D071 — nunca basta dizer "é um snapshot"; a
  Observação sempre diz *quando*, ex: "na abertura da viagem", "na emissão do CT-e"), e nunca mais
  sincronizado com o cadastro de origem, mesmo que ele mude depois (D073, reforço de D038).
- **Time Series** (ex: `POSICAO_VEICULO.LATITUDE`/`LONGITUDE`/`VELOCIDADE`): Origem = Capturado
  (rastreamento); alto volume (D049/D050) — ver
  [`../../information-model/HIGH_VOLUME_ENTITIES.md`](../../information-model/HIGH_VOLUME_ENTITIES.md).

## Como este documento cresce

Mesmo princípio de crescimento incremental de todo o projeto: cada arquivo `NNN-categoria.md` é
escrito quando explicitamente solicitado, na ordem do roadmap, nunca todos de uma vez.
