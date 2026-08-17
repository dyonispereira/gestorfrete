# 005 — Pneus

Atributos distintivos das 5 entidades de [`../../domain/005-pneus.md`](../../domain/005-pneus.md).
Atributos universais (D069), Padrões de atributo/Atributos Críticos (D077/D081) e a regra de que
indicadores agregados nunca são atributos operacionais (D090) não são repetidos aqui — ver
[`README.md`](./README.md). Máquina de estados canônica:
[`../../flows/004-PNEUS.md`](../../flows/004-PNEUS.md) (D035).

## 1. Ciclo completo — mapeamento com a máquina de estados

O ciclo pedido ("Compra → Estoque → Instalação → Rodagem → Rodízio → Recapagem → Nova instalação →
Nova recapagem → Sucata → Baixa") já é exatamente o fluxo principal de `004-PNEUS.md` — não precisa
de uma nova máquina de estados, só do mapeamento explícito entre fase de negócio e o que cada
entidade deste arquivo guarda em cada uma:

| Fase | Status do Pneu | O que é gravado, e onde |
|---|---|---|
| Compra | `COMPRADO` | `Pneu` (identidade ainda não finalizada — Marca de Fogo vem na fase seguinte) |
| Estoque | `EM_ESTOQUE` | `Pneu.MARCA_FOGO` aplicada; `Pneu.STATUS` |
| Instalação | `INSTALADO` | Novo `Posicionamento de Pneu` (`Vigente`) |
| Rodagem | `INSTALADO` (contínuo) | Nenhum registro novo por si só — acumula quilometragem, refletida em `Pneu.KM_CICLO_ATUAL`/`KM_ACUMULADO_TOTAL` (Derivado, D081) |
| Rodízio | `INSTALADO` (sem mudança de status) | `Posicionamento de Pneu` atual encerrado (`DATA_FIM`) + novo `Posicionamento de Pneu` criado — nunca edição do registro anterior (D037) |
| Recapagem | `AGUARDANDO_RECAPAGEM` → `EM_RECAPAGEM` | Novo `Registro de Recapagem`; `Posicionamento de Pneu` vigente é encerrado |
| Nova instalação | `EM_ESTOQUE` → `INSTALADO` | Repete a fase Instalação; `Pneu.NUMERO_RECAPAGENS_REALIZADAS` (Derivado) já reflete o ciclo anterior |
| Nova recapagem | Repete o ciclo | Novo `Registro de Recapagem`, `NUMERO_CICLO` incrementado — nunca decresce |
| Sucata | `SUCATA` | `Pneu.STATUS`; motivo obrigatório (D007) |
| Baixa | `BAIXADO` | `Pneu.STATUS`; soft delete nunca físico (D001) |

---

## Pneu

Dono: `maintenance` · Natureza: Transactional Data · Aggregate Root.

### 2. Marca de Fogo — identidade operacional, distinta do Código funcional

`PNEU.MARCA_FOGO` é a identidade que **sobrevive** a troca de posição, de veículo e a qualquer
número de recapagens — é ela, não o `PNEU.CODIGO` (D029/D030, formato configurável por tenant), que
o Almoxarife/Mecânico usam fisicamente para reconhecer o pneu no pátio. Os dois normalmente têm o
mesmo valor na prática, mas são conceitualmente distintos: `CODIGO` é a convenção de numeração do
sistema (pode mudar de formato por decisão do tenant, D030); `MARCA_FOGO` é a marcação física
gravada no pneu, que existe independentemente do GestorFrete e nunca muda de valor depois de
aplicada.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| PNEU.MARCA_FOGO | Marca de Fogo | Texto Curto | Sim, a partir de `EM_ESTOQUE` | Informado (Almoxarife, na entrada) | Não — imutável após aplicada | Interno | Único por tenant, para sempre (D084 — nunca reutilizada, mesmo após o pneu ser `BAIXADO`). **Atributo Crítico (D077)** — ver Governança abaixo |
| PNEU.MODELO_PNEU_ID | Modelo | Referência | Sim | Informado | Não | Interno | FK para Modelo de Pneu |
| PNEU.STATUS | Status | Enum | Sim | Calculado (transições da máquina de estados) | Sim, em `PneuStatusHistory` (D017/D018) | Interno | Valores e transições completas: `004-PNEUS.md` |
| PNEU.NUMERO_RECAPAGENS_REALIZADAS | Número de recapagens realizadas | Inteiro | Sim | Derivado (D081 — contagem de `Registro de Recapagem` com `RESULTADO = Aprovado`) | Não — projeção | Interno | Nunca editado diretamente; comparado contra `Política de Recapagem.NUMERO_MAXIMO_RECAPAGENS` para decidir `SUCATA` |

> **Posição não é atributo do Pneu (D096)**: repare que não existe `PNEU.POSICAO` nesta tabela — a
> posição pertence ao evento de instalação (`Posicionamento de Pneu`, abaixo), nunca ao Pneu em si.
> Isso evita inconsistência quando o pneu muda de veículo ou eixo: o Pneu nunca precisa ser
> "atualizado" por causa de um rodízio, só um novo `Posicionamento de Pneu` é criado.

### 4. Vida útil — composta, nunca um único atributo (D094)

A vida útil de um Pneu é a soma de cinco sinais distintos, cada um seu próprio
atributo/entidade — nunca um único campo "vida útil" que os resuma:

1. Quilometragem acumulada — `PNEU.KM_ACUMULADO_TOTAL` (abaixo)
2. Número de recapagens — `PNEU.NUMERO_RECAPAGENS_REALIZADAS` (acima)
3. Sulco — `Medição de Pneu` (histórica, abaixo)
4. Índice de desgaste — derivado da tendência de `Medição de Pneu` ao longo do tempo (calculado em
   `analytics`, D090 — não um campo próprio aqui)
5. Eventos de manutenção associados — `Item de Ordem de Serviço` onde `CATEGORIA_CUSTO = Pneus`
   referencia este Pneu ([`004-manutencao.md`](./004-manutencao.md))

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| PNEU.KM_ACUMULADO_TOTAL | Km acumulado (vida inteira) | Decimal | Sim | Derivado (D081 — soma de todos os `Posicionamento de Pneu` já encerrados + o vigente) | Não — projeção; fonte de verdade é `Posicionamento de Pneu` | Interno | Soma todos os ciclos, incluindo antes e depois de cada recapagem |
| PNEU.KM_CICLO_ATUAL | Km no ciclo atual | Decimal | Não | Derivado (D081 — desde a última instalação ou recapagem) | Não — projeção | Interno | Zera a cada nova Instalação (fase "Nova instalação" acima); usado para decidir `AGUARDANDO_RECAPAGEM` junto com o sulco |
| PNEU.SULCO_ATUAL_MM | Sulco atual (mm) | Decimal | Não | Derivado (D081 — última `Medição de Pneu` do tipo Sulco) | Não — projeção; fonte de verdade é `Medição de Pneu` (abaixo) | Interno | Lacuna do lote anterior **resolvida**: agora existe uma entidade histórica própria (`Medição de Pneu`, D092/D093), mesmo princípio que `Leitura de Hodômetro` já resolvia para o veículo (`003-frota.md`) |
| PNEU.SULCO_MINIMO_MM (via Modelo de Pneu) | Índice de condenação | Decimal | — | Ver `Modelo de Pneu`, abaixo | — | — | O limite não é do Pneu individual, é do Modelo — ver seção própria |

### 5. Custo — sempre derivado (D095)

O custo total e o custo por km nunca são digitados — são sempre a soma/razão de custos brutos já
registrados em outras entidades (D066/D090/D095): é uma propriedade calculada do próprio Pneu, não
uma estatística agregada de BI.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| PNEU.CUSTO_COMPRA | Custo de compra | Monetário | Sim | Informado (nota fiscal de entrada) | Não | Financeiro | Moeda: BRL (D075) |
| PNEU.CUSTO_ACUMULADO_TOTAL | Custo acumulado total | Monetário | Sim | Calculado (`CUSTO_COMPRA` + soma de `Registro de Recapagem.CUSTO` + soma de `Item de Ordem de Serviço.VALOR_TOTAL` onde `CATEGORIA_CUSTO = Pneus` referenciando este Pneu — ver [`004-manutencao.md`](./004-manutencao.md)) | Não — projeção | Financeiro | Moeda: BRL (D075). Persistido por justificativa de performance (D066) — recalcular a cada consulta seria caro dado o cruzamento com Itens de OS |
| PNEU.CUSTO_POR_KM | Custo por km | Decimal | Não | Calculado (`CUSTO_ACUMULADO_TOTAL / KM_ACUMULADO_TOTAL`) | Não | Financeiro | Unidade: BRL por km (D075 aplicado à unidade, não a um valor monetário simples). **Nunca informado manualmente — sempre calculado (D066)** |

### Governança do atributo crítico `MARCA_FOGO` (D077)

| Quem altera? | Quando muda? | Quem pode visualizar? | Quem nunca altera? |
|---|---|---|---|
| Almoxarife, apenas uma vez, na entrada em `EM_ESTOQUE` | Nunca muda depois de aplicada — mesmo que o pneu troque de posição, veículo ou passe por recapagens (D084) | Conforme RBAC | Todos os demais perfis e o próprio Almoxarife depois do registro inicial; Frontend não decide o valor (D027, o valor vem da leitura física do pneu) |

---

## Medição de Pneu (D092/D093 — nova nesta rodada)

Dono: `maintenance` · Natureza: Transactional Data · **Time Series** (D049/D050, D093) · Histórica
(D037/D083, D092) · Parte do agregado Pneu.

Toda medição recorrente ao longo do tempo — não só sulco, mas pressão, temperatura, balanceamento,
alinhamento e profundidade — passa a ter uma entidade histórica própria em vez de um campo "valor
atual" isolado no Pneu (D092), oficialmente classificada como Time Series (D093), assim como
`Posicao Veiculo`/`Leitura de Hodômetro` já eram tratadas.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| MEDICAO_PNEU.PNEU_ID | Pneu | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| MEDICAO_PNEU.TIPO_MEDICAO | Tipo de medição | Enum | Sim | Informado | **É ela própria o histórico** — nunca editada (D037) | Interno | Valores: Sulco/Pressão/Temperatura/Balanceamento/Alinhamento/Profundidade |
| MEDICAO_PNEU.VALOR | Valor | Decimal | Sim | Capturado (Mecânico/Almoxarife) ou Derivado (telemetria, quando disponível) | Não | Interno | Unidade depende de `TIPO_MEDICAO` (mm para Sulco/Profundidade, PSI para Pressão, °C para Temperatura) — sempre declarada junto ao valor, nunca implícita (D097 aplicado aqui por analogia, embora não seja monetário) |
| MEDICAO_PNEU.ORIGEM_MEDICAO | Origem da medição | Enum | Sim | Capturado (sistema) | Não | Interno | Valores: Manual/Checklist/Telemetria (futuro) |
| MEDICAO_PNEU.DATA_HORA | Data/hora da medição | Data/Hora | Sim | Capturado (sistema) | Não | Interno | Granularidade: segundo (D074); alto volume potencial — ver [`../../information-model/HIGH_VOLUME_ENTITIES.md`](../../information-model/HIGH_VOLUME_ENTITIES.md) |

---

## Posicionamento de Pneu

Dono: `maintenance` · Natureza: Transactional Data · Histórica (D037/D083) · Parte do agregado
Pneu.

### 3. Posição — parametrizável (D091), pertence à instalação, não ao Pneu (D096)

Um Enum fechado do tipo `Dianteiro Direito`/`Dianteiro Esquerdo`/`Traseiro Direito`/... não
sobrevive a um bitrem ou rodotrem, onde há múltiplas unidades (cavalo + 1 ou 2 implementos) cada
uma com sua própria contagem de eixos (4x2/6x2/6x4/8x2 no cavalo, 2 ou 3 eixos por implemento). Em
vez de um Enum, `POSICAO_CODIGO` segue uma convenção composicional, sempre válida independente da
configuração:

```
<UNIDADE>-<EIXO>-<LADO>[-<DUPLA>]
```

- `UNIDADE`: `CAVALO`, `IMPLEMENTO_1`, `IMPLEMENTO_2` (a unidade física dentro da Composição
  Veicular vigente, [`003-frota.md`](./003-frota.md) — 1 ou 2 implementos conforme bitrem/rodotrem)
- `EIXO`: número sequencial do eixo dentro daquela unidade (1, 2, 3...) — cardinalidade real vem da
  Ficha Técnica/Categoria de Veículo daquela unidade (4x2 tem 2 eixos no cavalo; 6x4 tem 3; etc.)
- `LADO`: `E` (esquerdo) ou `D` (direito)
- `DUPLA` (opcional): `INT`/`EXT`, apenas quando aquele eixo tem rodagem dupla

Exemplos válidos: `CAVALO-1-D` (dianteiro direito do cavalo, sempre simples), `CAVALO-2-D-INT`
(segundo eixo do cavalo, lado direito, roda interna da dupla), `IMPLEMENTO_1-3-E-EXT` (terceiro
eixo do primeiro implemento, lado esquerdo, roda externa). A mesma convenção cobre 4x2, 6x2, 6x4,
8x2, bitrem e rodotrem sem precisar de um valor novo por configuração — o `EIXO` simplesmente conta
até onde a Composição Veicular daquele veículo permitir.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| POSICIONAMENTO_PNEU.PNEU_ID | Pneu | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| POSICIONAMENTO_PNEU.VEICULO_TRACIONADOR_ID | Veículo Tracionador | Referência | Sim | Capturado (sistema) | Não | Interno | FK — sempre o cavalo mecânico, mesmo quando `POSICAO_CODIGO` indica um implemento (a Composição Veicular vigente resolve qual implemento) |
| POSICIONAMENTO_PNEU.POSICAO_CODIGO | Posição | Texto Curto | Sim | Informado (Mecânico, na instalação) | Não | Interno | Convenção descrita acima — parametrizável, nunca um Enum fixo |
| POSICIONAMENTO_PNEU.STATUS | Status | Enum | Sim | Calculado | Sim (append-only, D037) | Interno | Valores: `Vigente`/`Encerrado`. Invariante: no máximo um `Vigente` por Pneu (reforça "um pneu nunca em dois veículos ao mesmo tempo") |
| POSICIONAMENTO_PNEU.DATA_INICIO | Início da vigência | Data/Hora | Sim | Capturado (sistema) | Não | Interno | Granularidade: segundo (D074). Responde "Quando começou?" (D080) |
| POSICIONAMENTO_PNEU.DATA_FIM | Fim da vigência | Data/Hora | Não | Capturado (sistema, ao rodiziar/remover) | Não | Interno | Granularidade: segundo (D074). Responde "Quando terminou?" (D080) |
| POSICIONAMENTO_PNEU.ALTERADO_POR | Responsável | Referência | Sim | Capturado (sistema) | Não | Interno | Responde "Quem alterou?" (D080) — reforça D085: este relacionamento já é uma entidade de domínio própria, não uma FK simples, exatamente por ter início/fim/histórico/auditoria |
| POSICIONAMENTO_PNEU.KM_HODOMETRO_INICIO | Hodômetro do veículo no início | Decimal | Não | Capturado (referência a Leitura de Hodômetro, [`003-frota.md`](./003-frota.md)) | Não | Interno | Junto com `KM_HODOMETRO_FIM`, é o "km por ciclo" pedido no ponto 4 (Vida útil) — a diferença entre os dois |
| POSICIONAMENTO_PNEU.KM_HODOMETRO_FIM | Hodômetro do veículo no fim | Decimal | Não, preenchido ao encerrar | Capturado | Não | Interno | Idem acima |

---

## Registro de Recapagem

Dono: `maintenance` · Natureza: Transactional Data · Histórica (D037/D083) · Parte do agregado
Pneu.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| REGISTRO_RECAPAGEM.PNEU_ID | Pneu | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| REGISTRO_RECAPAGEM.NUMERO_CICLO | Número do ciclo de recapagem | Inteiro | Sim | Calculado (sequencial) | **É ela própria o histórico** (D037) | Interno | Nunca decresce para o mesmo Pneu |
| REGISTRO_RECAPAGEM.FORNECEDOR_ID | Recapadora | Referência | Sim | Informado | Não | Interno | FK para Fornecedor — [`001-cadastros.md`](./001-cadastros.md) |
| REGISTRO_RECAPAGEM.DATA_ENVIO | Data de envio | Data | Sim | Informado | Não | Interno | Granularidade: dia (D074) |
| REGISTRO_RECAPAGEM.DATA_RETORNO | Data de retorno | Data | Não | Informado | Não | Interno | Granularidade: dia (D074) |
| REGISTRO_RECAPAGEM.RESULTADO | Resultado | Enum | Não, obrigatório ao retornar | Informado (recapadora, via laudo) | Não | Interno | Valores: `Aprovado`/`Reprovado` |
| REGISTRO_RECAPAGEM.CUSTO | Custo da recapagem | Monetário | Sim | Informado (nota fiscal da recapadora) | Não | Financeiro | Moeda: BRL (D075) — ponto 5, Custo |

---

## Modelo de Pneu

Dono: `maintenance` · Natureza: Reference Data (D036) · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| MODELO_PNEU.FABRICANTE | Fabricante | Texto Curto | Sim | Informado | Não | Interno | |
| MODELO_PNEU.MEDIDA | Medida | Texto Curto | Sim | Informado | Não | Interno | Combinação Fabricante + Medida única por tenant |
| MODELO_PNEU.SULCO_MINIMO_MM | Índice de condenação (sulco mínimo, mm) | Decimal | Sim | Informado | Não | Interno | Ponto 4, Vida útil — limite abaixo do qual o Pneu deste modelo deve ir para `AGUARDANDO_RECAPAGEM`/sucata, independente de recapagens restantes |
| MODELO_PNEU.STATUS | Status | Enum | Sim | Informado | Não | Interno | Valores: `Ativo`/`Inativo` |

## Política de Recapagem

Dono: `maintenance` · Natureza: Reference Data (D036) · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| POLITICA_RECAPAGEM.MODELO_PNEU_ID | Modelo de Pneu | Referência | Não | Informado | Não | Interno | Opcional — política pode ser genérica (aplicada a todo tenant) ou específica por modelo |
| POLITICA_RECAPAGEM.NUMERO_MAXIMO_RECAPAGENS | Número máximo de recapagens | Inteiro | Sim | Informado | Não | Interno | Comparado contra `PNEU.NUMERO_RECAPAGENS_REALIZADAS` — maior ou igual a zero |
| POLITICA_RECAPAGEM.STATUS | Status | Enum | Sim | Informado | Não | Interno | Valores: `Ativa`/`Inativa` |

## Como este documento cresce

Mesmo princípio de todo o dicionário: um arquivo `NNN-categoria.md` por vez, na ordem do roadmap
(ver [`README.md`](./README.md)). Próximo: `006-financeiro.md`.
