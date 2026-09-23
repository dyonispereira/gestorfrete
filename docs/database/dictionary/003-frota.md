# 003 — Frota

Atributos distintivos das 10 entidades de [`../../domain/003-frota.md`](../../domain/003-frota.md).
Atributos universais (`ID`, `CODIGO`, `TENANT_ID`, `VERSAO`, `CRIADO_EM/POR`, `ATUALIZADO_EM/POR`,
`STATUS`) não são repetidos aqui (D069) — ver [`README.md`](./README.md), incluindo os novos
Padrões de atributo e Atributos Críticos (D077) usados neste arquivo.

## Reconciliação de nomes (D076)

O pedido de atenção especial citou tipos de Implemento: "carreta, bitrem, rodotrem, tanque, baú,
graneleiro, prancha, frigorífico, gaiola". Verificando `docs/domain/003-frota.md`, esses nove
termos descrevem **dois conceitos diferentes**, não um único atributo — reconciliados explicitamente
aqui em vez de criados como uma lista solta sem dono:

| Termo | Conceito real | Onde vive |
|---|---|---|
| Bitrem, Rodotrem | **Configuração de combinação veicular** (quantos Implementos, como acoplados) | `Composição Veicular` — `COMPOSICAO_VEICULAR.TIPO_COMBINACAO` |
| Carreta, Tanque, Baú, Graneleiro, Prancha, Frigorífico, Gaiola | **Tipo de carroceria do próprio Implemento** | `Implemento` — `IMPLEMENTO.TIPO_CARROCERIA` |

"Carreta" é ambíguo em linguagem coloquial (às vezes usado para "Implemento" em geral, às vezes
para o tipo específico de carroceria plana/grade) — no GestorFrete, **Implemento** é sempre o nome
de entidade (D028); "Carreta" só aparece como um valor possível de `TIPO_CARROCERIA`, nunca como
sinônimo do nome da entidade em documentação técnica.

---

## Veículo Tracionador (Cavalo Mecânico)

Dono: `fleet` · Natureza: Master Data · Aggregate Root.

O pedido de atenção especial ("separar claramente: identidade do veículo; características
técnicas; documentação; operacional; rastreamento; telemetria") mapeia para entidades e bounded
contexts distintos — não para seis grupos de colunas dentro de uma única tabela, na prática do
D033/D034 (posse única por atributo/entidade):

| Grupo pedido | Onde vive de fato |
|---|---|
| Identidade | Atributos da própria raiz Veículo Tracionador (tabela abaixo) |
| Características técnicas | Entidade filha **Ficha Técnica do Veículo** (seção própria abaixo) |
| Documentação | Entidades filhas **Documento do Veículo**, **Licenciamento do Veículo**, **Apólice de Seguro Veicular** (seções próprias abaixo) |
| Operacional | Entidade filha **Leitura de Hodômetro** (histórico) + read model **Disponibilidade do Veículo** (estado atual, D079) |
| Rastreamento / Telemetria | **Ainda não modelado como entidade própria** — pertence ao bounded context `tracking` (`docs/database/dictionary/008-rastreamento.md`, planejado, não escrito). O Veículo Tracionador nunca guarda posição/telemetria bruta diretamente; apenas seria referenciado por ID a partir de `tracking` (D033/D034) — antecipado aqui para não ser esquecido quando aquele arquivo for escrito |

### Atributos (Identidade — Dados Permanentes, D078)

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| VEICULO_TRACIONADOR.PLACA | Placa | Texto Curto | Sim | Informado | Não (troca de placa gera nova auditoria, não sobrescrita silenciosa) | Interno | Único por tenant. **Atributo Crítico (D077)** — ver Governança abaixo |
| VEICULO_TRACIONADOR.RENAVAM | RENAVAM | Texto Curto | Sim | Informado | Não | Interno | Único por tenant |
| VEICULO_TRACIONADOR.FABRICANTE | Fabricante | Texto Curto | Sim | Informado | Não | Interno | |
| VEICULO_TRACIONADOR.MODELO | Modelo | Texto Curto | Sim | Informado | Não | Interno | |
| VEICULO_TRACIONADOR.ANO_FABRICACAO | Ano de fabricação | Inteiro | Sim | Informado | Não | Interno | |
| VEICULO_TRACIONADOR.CATEGORIA_VEICULO_ID | Categoria | Referência | Sim | Informado | Não | Interno | FK para Categoria de Veículo |
| VEICULO_TRACIONADOR.FILIAL_ID | Filial | Referência | Não | Informado | Não | Interno | Opcional, mas comum |

### Governança do atributo crítico `PLACA` (D077)

| Quem altera? | Quando muda? | Quem pode visualizar? | Quem nunca altera? |
|---|---|---|---|
| Analista de Frota/Gestor Operacional, via processo de troca de placa (rara, ex: mudança de estado/categoria) | Somente em evento formal de reemplacamento — nunca em edição casual de cadastro | Conforme RBAC | Frontend sozinho (regra crítica no backend, D027); Motorista (app apenas consulta) |

### Nunca armazenado diretamente aqui: dados de Pneu

Por posse única (D033/D034), o Veículo Tracionador **nunca** guarda informação de pneu
diretamente — nem modelo, nem posição, nem vida útil. Ele é apenas referenciado a partir de
**Posicionamento de Pneu** ([`../../domain/005-pneus.md`](../../domain/005-pneus.md), dono
`maintenance`), que sabe qual Pneu está instalado em qual posição deste veículo. Consultar
`005-pneus.md` (dicionário, planejado) para os atributos de Pneu propriamente ditos.

---

## Implemento

Dono: `fleet` · Natureza: Master Data · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| IMPLEMENTO.PLACA | Placa | Texto Curto | Sim | Informado | Não | Interno | Único por tenant |
| IMPLEMENTO.RENAVAM | RENAVAM | Texto Curto | Sim | Informado | Não | Interno | Único por tenant |
| IMPLEMENTO.TIPO_CARROCERIA | Tipo de carroceria | Enum | Sim | Informado | Não | Interno | Valores: Carreta/Tanque/Baú/Graneleiro/Prancha/Frigorífico/Gaiola — ver Reconciliação de nomes acima (D076). Lista fechada mas extensível; valores iniciais são de referência, crescem conforme a operação exigir |
| IMPLEMENTO.CATEGORIA_VEICULO_ID | Categoria | Referência | Sim | Informado | Não | Interno | FK para Categoria de Veículo |
| IMPLEMENTO.CAPACIDADE_CARGA | Capacidade de carga | Decimal | Sim | Informado | Não | Interno | Em kg ou m³, conforme `TIPO_CARROCERIA` |
| IMPLEMENTO.STATUS_DISPONIBILIDADE | Status | Enum | Sim | Calculado | Não | Interno | Valores: `Disponível`/`Em Uso`/`Inativo` |

---

## Composição Veicular

Dono: `fleet` · Natureza: Transactional Data · Aggregate Root.

Registra a combinação Veículo Tracionador + Implemento(s) — este é o ponto certo para `TIPO_COMBINACAO`
(bitrem/rodotrem, ver Reconciliação de nomes acima) e para a associação temporal exigida por D080,
distinta e mais duradoura que a Alocação de Recurso de uma Viagem específica
([`002-operacao.md`](./002-operacao.md), que é por viagem).

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| COMPOSICAO_VEICULAR.VEICULO_TRACIONADOR_ID | Veículo Tracionador | Referência | Sim | Informado | Não | Interno | FK |
| COMPOSICAO_VEICULAR.TIPO_COMBINACAO | Tipo de combinação | Enum | Sim | Informado/Calculado (número de Implementos) | Não | Interno | Valores: Simples/Bitrem/Rodotrem — ver Reconciliação de nomes acima (D076) |
| COMPOSICAO_VEICULAR.EIXOS_TOTAL | Total de eixos | Inteiro | Sim | Calculado (soma dos eixos de cada unidade) | Não | Interno | Usado na validação CONTRAN |
| COMPOSICAO_VEICULAR.STATUS | Status | Enum | Sim | Calculado | Não | Interno | Valores: `Válida`/`Inválida` |
| COMPOSICAO_VEICULAR.DATA_INICIO_VIGENCIA | Início da vigência da combinação | Data/Hora | Sim | Capturado (sistema) | Não | Interno | Granularidade: segundo (D074). Responde "Quando começou?" (D080) |
| COMPOSICAO_VEICULAR.DATA_FIM_VIGENCIA | Fim da vigência da combinação | Data/Hora | Não | Capturado (sistema, ao desfazer a composição) | Não | Interno | Granularidade: segundo (D074). Responde "Quando terminou?" (D080) |
| COMPOSICAO_VEICULAR.ALTERADO_POR | Responsável pela alteração | Referência | Sim | Capturado (sistema) | Não | Interno | Responde "Quem alterou?" (D080) |

> Associação Veículo × Motorista e Cavalo × Implemento **por viagem** (mais volátil que a
> Composição Veicular padrão da frota) já está coberta por `ALOCACAO_RECURSO_VIAGEM` em
> [`002-operacao.md`](./002-operacao.md), que também responde as três perguntas de D080 via
> `Vigente`/`Substituída` append-only — não duplicado aqui.

---

## Ficha Técnica do Veículo

Dono: `fleet` · Natureza: Master Data · Parte do agregado Veículo Tracionador · Dados
Permanentes (D078).

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| FICHA_TECNICA_VEICULO.CHASSI | Chassi | Texto Curto | Sim | Informado | Não | Interno | Único por tenant |
| FICHA_TECNICA_VEICULO.MOTOR | Motor | Texto Curto | Não | Informado | Não | Interno | |
| FICHA_TECNICA_VEICULO.EIXOS | Eixos | Inteiro | Sim | Informado | Não | Interno | |
| FICHA_TECNICA_VEICULO.TARA | Tara (peso do veículo vazio) | Decimal | Sim | Informado | Não | Interno | Em kg |
| FICHA_TECNICA_VEICULO.CAPACIDADE_CARGA | Capacidade de carga | Decimal | Sim | Informado | Não | Interno | Em kg |
| FICHA_TECNICA_VEICULO.PBT | Peso Bruto Total (PBT) | Decimal | Sim | Informado | Não | Interno | Em kg — limite regulatório usado na validação de Composição Veicular |
| FICHA_TECNICA_VEICULO.RNTRC_PROPRIETARIO | RNTRC do proprietário | Texto Curto | Não | Informado | Não | Fiscal | Registro Nacional de Transportadores Rodoviários de Cargas (ANTT) do proprietário do veículo — pode ser o próprio tenant ou o Motorista autônomo dono do cavalo (ver `MOTORISTA.TIPO_VINCULO` em [`001-cadastros.md`](./001-cadastros.md)); não é uma nova entidade, é um atributo referencial |
| FICHA_TECNICA_VEICULO.COMBUSTIVEL | Tipo de combustível | Enum | Sim | Informado | Não | Interno | Valores: Diesel S10/Diesel S500/GNV/Elétrico |

---

## Documento do Veículo

Dono: `fleet` · Natureza: Transactional Data · Parte do agregado Veículo Tracionador.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| DOCUMENTO_VEICULO.VEICULO_TRACIONADOR_ID | Veículo Tracionador | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| DOCUMENTO_VEICULO.TIPO | Tipo de documento | Enum | Sim | Informado | Não | Interno | Ex: CRLV |
| DOCUMENTO_VEICULO.NUMERO | Número | Texto Curto | Sim | Informado | Não | Interno | |
| DOCUMENTO_VEICULO.DATA_VALIDADE | Validade | Data | Sim | Informado | Não | Interno | Granularidade: dia (D074); deve ser futura no cadastro |
| DOCUMENTO_VEICULO.STATUS | Status | Enum | Sim | Calculado (a partir da validade) | Não | Interno | Valores: `Válido`/`Vencido` |
| DOCUMENTO_VEICULO.ARQUIVO_ID | Documento digitalizado | Arquivo | Não | Informado | Não | Interno | Anexo — D024 |

## Apólice de Seguro Veicular

Dono: `fleet` · Natureza: Transactional Data · Parte do agregado Veículo Tracionador.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| APOLICE_SEGURO_VEICULAR.VEICULO_TRACIONADOR_ID | Veículo Tracionador | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| APOLICE_SEGURO_VEICULAR.SEGURADORA_ID | Seguradora | Referência | Sim | Informado | Não | Interno | FK — ver [`001-cadastros.md`](./001-cadastros.md) |
| APOLICE_SEGURO_VEICULAR.NUMERO_APOLICE | Número da apólice | Texto Curto | Sim | Informado | Não | Interno | |
| APOLICE_SEGURO_VEICULAR.VIGENCIA_INICIO | Início da vigência | Data | Sim | Informado | Não | Interno | Granularidade: dia (D074) |
| APOLICE_SEGURO_VEICULAR.VIGENCIA_FIM | Fim da vigência | Data | Sim | Informado | Não | Interno | Granularidade: dia (D074); deve ser posterior ao início |
| APOLICE_SEGURO_VEICULAR.STATUS | Status | Enum | Sim | Calculado | Não | Interno | Valores: `Vigente`/`Vencida` |

## Leitura de Hodômetro

Dono: `fleet` · Natureza: Transactional Data · Histórica (D037) · Parte do agregado Veículo
Tracionador · Dado Operacional (D078).

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| LEITURA_HODOMETRO.VEICULO_TRACIONADOR_ID | Veículo Tracionador | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| LEITURA_HODOMETRO.VALOR_KM | Valor do hodômetro | Decimal | Sim | Capturado (abastecimento/checklist/manual/despacho-encerramento de Viagem) | **É ela própria o histórico** — nunca editada, apenas inserida (D037) | Interno | Invariante: nunca menor que a última leitura do mesmo veículo |
| LEITURA_HODOMETRO.ORIGEM | Origem da leitura | Enum | Sim | Capturado (sistema) | Não | Interno | Valores: Abastecimento/Checklist/Manual/Telemetria/Ordem de Serviço/**Despacho de Viagem/Encerramento de Viagem** (os dois últimos, **Reconciliado, V1 Operational Hardening, Parte 2** — coluna física é `String` livre, sem CHECK, sem migration para os dois novos valores) |
| LEITURA_HODOMETRO.VIAGEM_ID | Viagem associada | Referência | Não | Capturado (sistema) | Não | Interno | Quando a leitura ocorre no contexto de uma Viagem específica — origem funcional de `KM_INICIAL`/`KM_FINAL` (D077, atributos críticos citados como exemplo): a leitura `ORIGEM=Despacho de Viagem` é o `KM_INICIAL`, a `ORIGEM=Encerramento de Viagem` é o `KM_FINAL` (**Reconciliado, V1 Operational Hardening, Parte 2** — antes um conceito ilustrativo de "primeira/última leitura cronológica", agora pareamento exato por `ORIGEM`, gravado por `TripOdometerRecorder`); não são campos próprios da Viagem, são a leitura de fronteira desta entidade histórica |
| LEITURA_HODOMETRO.DATA_HORA | Data/hora da leitura | Data/Hora | Sim | Capturado (sistema) | Não | Interno | Granularidade: segundo (D074) |

## Licenciamento do Veículo

Dono: `fleet` · Natureza: Transactional Data · Parte do agregado Veículo Tracionador.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| LICENCIAMENTO_VEICULO.VEICULO_TRACIONADOR_ID | Veículo Tracionador | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| LICENCIAMENTO_VEICULO.EXERCICIO | Exercício (ano) | Inteiro | Sim | Informado | Não | Interno | Único por veículo por exercício |
| LICENCIAMENTO_VEICULO.VALOR_PAGO | Valor pago | Monetário | Não | Informado | Não | Financeiro | Moeda: BRL (D075) |
| LICENCIAMENTO_VEICULO.DATA_QUITACAO | Data de quitação | Data | Não | Informado | Não | Interno | Granularidade: dia (D074) |
| LICENCIAMENTO_VEICULO.STATUS | Status | Enum | Sim | Calculado | Não | Interno | Valores: `Pendente`/`Quitado`/`Vencido` |

## Categoria de Veículo

Dono: `fleet` · Natureza: Reference Data (D036) · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| CATEGORIA_VEICULO.NOME | Nome | Texto Curto | Sim | Informado | Não | Interno | Único por tenant. Ex: Truck, Carreta, Bitrem — nível de classificação administrativa, distinto de `TIPO_COMBINACAO` (que é técnico/regulatório) |
| CATEGORIA_VEICULO.STATUS | Status | Enum | Sim | Informado | Não | Interno | Valores: `Ativa`/`Inativa` |

## Disponibilidade do Veículo

Dono: `fleet` · Natureza: Read Model (projeção, não transacional) · Estado Atual (D079) — nunca a
fonte de verdade de nenhum dos estados que resume.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| DISPONIBILIDADE_VEICULO.VEICULO_TRACIONADOR_ID | Veículo Tracionador | Referência | Sim | Capturado (sistema) | Não | Interno | FK 1:1, imutável |
| DISPONIBILIDADE_VEICULO.STATUS | Status consolidado | Enum | Sim | Derivado (eventos de `freight`/`maintenance`, D032) | Não — é a própria projeção, sempre o valor mais recente | Interno | Valores: `Disponível`/`Em Viagem`/`Em Manutenção`/`Inativo`. **Ter este campo não elimina o histórico** (D079) — o histórico completo de cada dimensão vive em `ViagemStatusHistory` ([`002-operacao.md`](./002-operacao.md)) e na Ordem de Serviço (`004-manutencao.md`, planejado), nunca aqui |
| DISPONIBILIDADE_VEICULO.MOTORISTA_ATUAL_ID | Motorista atual | Referência | Não | Derivado (Alocação de Recurso da Viagem `Vigente`) | Não — projeção do valor atual | Interno | O histórico de trocas vive em `ALOCACAO_RECURSO_VIAGEM` ([`002-operacao.md`](./002-operacao.md)), que responde D080 — este campo é só o atalho de leitura rápida (D079) |
| DISPONIBILIDADE_VEICULO.IMPLEMENTO_ATUAL_ID | Implemento atual | Referência | Não | Derivado (Alocação de Recurso da Viagem `Vigente` ou Composição Veicular vigente) | Não | Interno | Mesma lógica do campo acima |
| DISPONIBILIDADE_VEICULO.ATUALIZADO_EM | Última recomputação | Data/Hora | Sim | Capturado (sistema) | Não | Interno | Granularidade: segundo (D074) — quando a projeção foi recalculada pela última vez, não "quem alterou" (ninguém altera diretamente, D032) |

## Como este documento cresce

Mesmo princípio de todo o dicionário: um arquivo `NNN-categoria.md` por vez, na ordem do roadmap
(ver [`README.md`](./README.md)). Próximo: `004-manutencao.md`.
