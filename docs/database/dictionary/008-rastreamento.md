# 008 — Rastreamento

Atributos distintivos das 9 entidades de
[`../../domain/008-rastreamento.md`](../../domain/008-rastreamento.md) (ver aquele arquivo para a
reconciliação D076 contra a lista originalmente estimada). Atributos universais (D069), Padrões de
atributo/Atributos Críticos (D077/D081) e a regra de indicadores nunca operacionais (D090) não são
repetidos aqui — ver [`README.md`](./README.md).

Dez decisões atravessam este arquivo inteiro: **D117** (toda posição declara sua Fonte), **D118**
(metadados de qualidade, quando disponíveis), **D120** (telemetria nunca assume um conjunto fixo de
sensores — implementado como tipo de sensor extensível + valor, nunca uma coluna por sensor),
**D121/D123** (nada aqui é editado depois de inserido — só se acrescenta), **D124/D125** (captura,
recebimento e processamento são três momentos distintos, sempre que o dado vem de fonte externa —
nunca um único `DATA_HORA`), **D126** (ausência de um sensor nunca invalida a leitura), **D127**
(todo Evento de Rastreamento tem severidade) e **D128** (um Veículo pode ter múltiplos Equipamentos
de Rastreamento simultâneos, um por papel).

---

## Provedor de Rastreamento

Dono: `tracking` · Natureza: Reference Data (D036) · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| PROVEDOR_RASTREAMENTO.NOME | Nome | Texto Curto | Sim | Informado | Não | Interno | Único por tenant — ex: Omnilink, Sascar, Autotrac, Positron, OnixSat, Cobli, Maxtrack |
| PROVEDOR_RASTREAMENTO.STATUS | Status | Enum | Sim | Informado | Não | Interno | Valores: `Ativo`/`Inativo` |

## Equipamento de Rastreamento

Dono: `tracking` · Natureza: Master Data · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| EQUIPAMENTO_RASTREAMENTO.PROVEDOR_RASTREAMENTO_ID | Provedor | Referência | Sim | Informado | Não | Interno | FK |
| EQUIPAMENTO_RASTREAMENTO.IDENTIFICADOR_SERIAL | Identificador (serial/IMEI) | Texto Curto | Sim | Informado | Não | Interno | Único globalmente (não só por tenant — é um dado físico do equipamento); nunca reutilizado (D084) |
| EQUIPAMENTO_RASTREAMENTO.TIPO_EQUIPAMENTO | Papel do equipamento | Enum | Sim | Informado | Não | Interno | D128 — Valores: `Principal`/`Backup`/`Câmera`/`Sensor de Temperatura`/`TPMS`/`Outro`. Um Veículo pode ter N Equipamentos simultâneos, cada um com seu papel; no máximo um `Principal` vigente |
| EQUIPAMENTO_RASTREAMENTO.VEICULO_TRACIONADOR_ID | Veículo Tracionador vigente | Referência | Não | Capturado (sistema) | Sim, via vínculo temporal abaixo | Interno | Dado vivo — aponta para o veículo atual; N:1 — vários Equipamentos (de papéis distintos) podem apontar para o mesmo Veículo ao mesmo tempo (D128) |
| EQUIPAMENTO_RASTREAMENTO.DATA_INICIO_VIGENCIA | Início da instalação | Data/Hora | Não | Capturado (sistema) | Não | Interno | Granularidade: segundo (D074). Responde "Quando começou?" (D080) |
| EQUIPAMENTO_RASTREAMENTO.DATA_FIM_VIGENCIA | Fim da instalação | Data/Hora | Não | Capturado (sistema, ao remover/trocar) | Não | Interno | Responde "Quando terminou?" (D080) |
| EQUIPAMENTO_RASTREAMENTO.ALTERADO_POR | Responsável | Referência | Não | Capturado (sistema) | Não | Interno | Responde "Quem alterou?" (D080) |
| EQUIPAMENTO_RASTREAMENTO.STATUS | Status | Enum | Sim | Calculado | Sim | Interno | Valores: `Ativo`/`Inativo`/`Removido` |

## Origem de Localização

Dono: `tracking` · Natureza: Reference Data (D036, candidata a Platform Reference Data, D046) ·
Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| ORIGEM_LOCALIZACAO.NOME | Nome | Texto Curto | Sim | Informado | Não | Interno | Valores típicos (D117): GPS/GSM/Satélite/Wi-Fi/BLE/Manual/API Externa — catálogo, não Enum fechado no código, para admitir fontes novas sem alteração de sistema |
| ORIGEM_LOCALIZACAO.PRECISAO_TIPICA_METROS | Precisão típica (m) | Decimal | Não | Informado | Não | Interno | Metadado de referência — a precisão real de cada leitura vive em `POSICAO_VEICULO.PRECISAO_METROS` (D118), este campo é só a expectativa típica da fonte |

---

## Posição de Veículo

Dono: `tracking` · Natureza: Transactional Data · **Time Series** (D049/D050) · Histórica (D037,
D121) desde a concepção · Aggregate Root.

Por pedido explícito, esta entidade recebe tratamento equivalente ao dado à Viagem — é uma das mais
consultadas do sistema, e cada atributo aqui é, por definição, uma fotografia imutável (nunca "o
veículo agora", sempre "o veículo neste instante").

### Atributos

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| POSICAO_VEICULO.VEICULO_TRACIONADOR_ID | Veículo | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| POSICAO_VEICULO.EQUIPAMENTO_RASTREAMENTO_ID | Equipamento de origem | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| POSICAO_VEICULO.LATITUDE | Latitude | Decimal | Sim | Capturado (Equipamento) | Não | Interno | Parte do tipo Localização, junto com Longitude |
| POSICAO_VEICULO.LONGITUDE | Longitude | Decimal | Sim | Capturado (Equipamento) | Não | Interno | |
| POSICAO_VEICULO.DATA_HORA_CAPTURA | Data/hora de captura | Data/Hora | Sim | Capturado (Equipamento — relógio do próprio dispositivo) | Não | Interno | D125 — o instante real da leitura no campo; granularidade segundo ou milissegundo (D074) |
| POSICAO_VEICULO.DATA_HORA_RECEBIMENTO | Data/hora de recebimento | Data/Hora | Sim | Capturado (sistema, ao receber o pacote do Provedor) | Não | Interno | D124/D125 — distinto da captura; a diferença entre os dois mede o atraso de comunicação |
| POSICAO_VEICULO.DATA_HORA_PROCESSAMENTO | Data/hora de processamento | Data/Hora | Sim | Capturado (sistema, ao persistir/interpretar) | Não | Interno | D125 — terceiro momento; normalmente muito próximo do recebimento, mas nunca assumido como igual |
| POSICAO_VEICULO.ORIGEM_LOCALIZACAO_ID | Fonte | Referência | Sim | Capturado (Equipamento) | Não | Interno | D117 — nunca ausente; toda posição sabe de onde veio |
| POSICAO_VEICULO.PRECISAO_METROS | Precisão (m) | Decimal | Não | Capturado (Equipamento, quando informado) | Não | Interno | D118 — nem todo Provedor envia; ausente é `null`, não zero |
| POSICAO_VEICULO.NUMERO_SATELITES | Número de satélites | Inteiro | Não | Capturado (Equipamento, quando informado) | Não | Interno | D118 |
| POSICAO_VEICULO.HDOP | HDOP | Decimal | Não | Capturado (Equipamento, quando informado) | Não | Interno | D118 — Horizontal Dilution of Precision, quanto menor, melhor a geometria dos satélites |
| POSICAO_VEICULO.NIVEL_CONFIANCA | Nível de confiança | Percentual | Não | Calculado (a partir de Precisão/HDOP/Satélites, quando disponíveis) | Não | Interno | D118 — síntese opcional dos metadados de qualidade acima, quando o Provedor não fornece os componentes individuais |

### Governança de Posição de Veículo (tratamento especial pedido)

| Atributo | Origem | Alterável? | Histórico | Observação |
|---|---|---|---|---|
| Latitude | Rastreador (Equipamento) | Não — nunca editado, só um novo registro | Sim — cada leitura é uma linha nova | Time Series (D049/D050) |
| Longitude | Rastreador (Equipamento) | Não | Sim | Time Series |
| Data/Hora de Captura | Rastreador (Equipamento) | Não | Sim | D125 — o instante real da leitura, distinto do recebimento |
| Data/Hora de Recebimento | Sistema (chegada do pacote) | Não | Sim | D124/D125 — mede atraso de comunicação junto com a Captura |
| Data/Hora de Processamento | Sistema (persistência) | Não | Sim | D125 — terceiro momento, não assumido igual ao recebimento |
| Fonte | Rastreador (Equipamento) | Não | Sim | D117 — nunca ausente |
| Precisão / Satélites / HDOP | Rastreador (Equipamento) | Não | Sim | D118 — opcionais, ausentes quando o Provedor não envia |
| Nível de Confiança | Calculado | Não | Sim | Derivado dos metadados acima (D118); nunca informado manualmente |

Nenhuma linha desta tabela tem "Quem pode alterar" diferente de "ninguém" — ao contrário da Viagem,
Posição de Veículo não tem um ciclo de aprovação/edição humana: ela nasce pronta, de uma única fonte
(o Equipamento), e nunca é tocada de novo (D121). É esse fato — zero mutabilidade, 100% do valor no
"quando" — que a torna tão diferente de qualquer entidade cadastral já documentada.

---

## Leitura de Telemetria

Dono: `tracking` · Natureza: Transactional Data · **Time Series** (D049/D050) · Histórica (D037,
D121) · Aggregate Root.

Por D120, esta entidade **não tem uma coluna por sensor** — isso exigiria alteração estrutural a
cada novo tipo de sensor. Em vez disso, cada leitura é uma linha com um `TIPO_SENSOR` extensível +
um `VALOR`, mesmo padrão já usado em `Medição de Pneu` (D092/D093, [`005-pneus.md`](./005-pneus.md)).

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| LEITURA_TELEMETRIA.VEICULO_TRACIONADOR_ID | Veículo | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| LEITURA_TELEMETRIA.EQUIPAMENTO_RASTREAMENTO_ID | Equipamento de origem | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| LEITURA_TELEMETRIA.POSICAO_VEICULO_ID | Posição associada | Referência | Não | Capturado (sistema, quando o mesmo pacote trouxe posição e telemetria) | Não | Interno | Opcional — não força acoplamento quando o Provedor envia telemetria e posição separadamente |
| LEITURA_TELEMETRIA.TIPO_SENSOR | Tipo de sensor | Enum | Sim | Capturado (Equipamento) | **É ela própria o histórico** — nunca editada (D037/D121) | Interno | D120 — vocabulário aberto a crescimento: Ignição/Velocidade/Bateria/Tensão/Odômetro/Horímetro/RPM/Temperatura/Combustível/Aceleração/Frenagem hoje; Pressão dos Pneus/Sensor ABS/Eixo Levantado/Porta Aberta/Sensor de Fadiga/Câmera IA amanhã, sem alteração estrutural |
| LEITURA_TELEMETRIA.VALOR | Valor | Decimal | Sim | Capturado (Equipamento) | Não | Interno | Unidade depende de `TIPO_SENSOR` |
| LEITURA_TELEMETRIA.UNIDADE | Unidade | Texto Curto | Sim | Capturado (Equipamento) | Não | Interno | Ex: km/h, %, V, RPM, °C, L, m/s² — sempre declarada junto ao valor (D097 aplicado por analogia) |
| LEITURA_TELEMETRIA.DATA_HORA_CAPTURA | Data/hora de captura | Data/Hora | Sim | Capturado (Equipamento) | Não | Interno | D125. Granularidade: segundo (D074) |
| LEITURA_TELEMETRIA.DATA_HORA_RECEBIMENTO | Data/hora de recebimento | Data/Hora | Sim | Capturado (sistema) | Não | Interno | D124/D125 |
| LEITURA_TELEMETRIA.DATA_HORA_PROCESSAMENTO | Data/hora de processamento | Data/Hora | Sim | Capturado (sistema) | Não | Interno | D125 |

## Heartbeat

Dono: `tracking` · Natureza: Transactional Data · Técnica/observacional (D105 aplicado por
analogia) · Histórica (D037, D113/D121) · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| HEARTBEAT.EQUIPAMENTO_RASTREAMENTO_ID | Equipamento | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| HEARTBEAT.PROTOCOLO_EXTERNO | Identificador do pacote (chave de idempotência) | Texto Curto | Não | Capturado (Provedor) | Não | Interno | D111 — quando o Provedor oferece um identificador de sequência; evita duplo processamento do mesmo pacote |
| HEARTBEAT.DATA_HORA_ENVIO | Data/hora de envio | Data/Hora | Não | Capturado (Equipamento, quando informado) | Não | Interno | D125, quando disponível |
| HEARTBEAT.DATA_HORA_RECEBIMENTO | Data/hora de recebimento | Data/Hora | Sim | Capturado (sistema) | Não | Interno | D124/D125 — sempre presente, mesmo quando o envio não é informado pelo Provedor |

---

## Cerca Eletrônica (Geofence)

Dono: `tracking` · Natureza: Reference Data (D036) — **configuração, não histórico (D122)** ·
Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| CERCA_ELETRONICA.NOME | Nome | Texto Curto | Sim | Informado | Não | Interno | Único por tenant |
| CERCA_ELETRONICA.TIPO_GEOMETRIA | Tipo de geometria | Enum | Sim | Informado | Não | Interno | Valores: `Círculo`/`Polígono` |
| CERCA_ELETRONICA.CENTRO | Centro (quando Círculo) | Localização | Não, obrigatório se `TIPO_GEOMETRIA = Círculo` | Informado | Não | Interno | |
| CERCA_ELETRONICA.RAIO_METROS | Raio em metros (quando Círculo) | Decimal | Não, obrigatório se `TIPO_GEOMETRIA = Círculo` | Informado | Não | Interno | Maior que zero |
| CERCA_ELETRONICA.POLIGONO | Vértices (quando Polígono) | JSON Estruturado | Não, obrigatório se `TIPO_GEOMETRIA = Polígono` | Informado | Não | Interno | Ao menos 3 pontos, polígono fechado |
| CERCA_ELETRONICA.CLIENTE_ID / FILIAL_ID | Local de negócio associado | Referência | Não | Informado | Não | Interno | Opcional — quando a cerca representa um ponto conhecido |
| CERCA_ELETRONICA.STATUS | Status | Enum | Sim | Informado | Não | Interno | Valores: `Ativa`/`Inativa` |

## Evento de Rastreamento

Dono: `tracking` · Natureza: Transactional Data · Histórica (D037/D121) · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| EVENTO_RASTREAMENTO.VEICULO_TRACIONADOR_ID | Veículo | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| EVENTO_RASTREAMENTO.TIPO | Tipo | Enum | Sim | Calculado (regra de detecção sobre Posição/Telemetria) | **É ele próprio o histórico** (D037) | Interno | Valores: `ParadaDetectada`/`DesvioDeRotaDetectado`/`ExcessoDeVelocidade`/`EntrouGeofence`/`SaiuGeofence`/`IgnicaoLigada`/`IgnicaoDesligada` — consolidação D076, ver `008-rastreamento.md` |
| EVENTO_RASTREAMENTO.POSICAO_VEICULO_ID | Posição de origem | Referência | Não | Capturado (sistema) | Não | Interno | D119 — o Evento é sempre derivado de uma leitura bruta e a referencia; a leitura original nunca é substituída |
| EVENTO_RASTREAMENTO.CERCA_ELETRONICA_ID | Cerca Eletrônica | Referência | Não, obrigatório quando `TIPO` envolve geofence | Capturado (sistema) | Não | Interno | D122 — o Evento registra apenas o fato (entrou/saiu); a "permanência" é a diferença entre um par Entrou/Saiu, calculada em `analytics` (D090), nunca um terceiro tipo persistido |
| EVENTO_RASTREAMENTO.CONFIGURACAO_LIMITE_VELOCIDADE_ID | Configuração de limite aplicada | Referência | Não, obrigatório quando `TIPO = ExcessoDeVelocidade` | Capturado (sistema) | Não | Interno | |
| EVENTO_RASTREAMENTO.VALOR_DETECTADO | Valor que disparou a detecção | Decimal | Não | Capturado (cópia do valor da Posição/Telemetria de origem, ex: a velocidade registrada) | Não | Interno | D119 — cópia para consulta rápida; a leitura original em `POSICAO_VEICULO_ID`/`LEITURA_TELEMETRIA` permanece a fonte de verdade |
| EVENTO_RASTREAMENTO.SEVERIDADE | Severidade | Enum | Sim | Calculado (regra de classificação por `TIPO`/magnitude do desvio) | Não | Interno | D127 — Valores: `Informação`/`Atenção`/`Alerta`/`Crítico`. Permite priorização de notificação sem depender só do `TIPO` |
| EVENTO_RASTREAMENTO.DATA_HORA | Data/hora | Data/Hora | Sim | Capturado (sistema) | Não | Interno | Granularidade: segundo (D074) |

## Configuração de Limite de Velocidade

Dono: `tracking` · Natureza: Reference Data (D036) · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| CONFIGURACAO_LIMITE_VELOCIDADE.CATEGORIA_VEICULO_ID | Categoria de Veículo | Referência | Não | Informado | Não | Interno | Opcional — ausente = limite geral do tenant |
| CONFIGURACAO_LIMITE_VELOCIDADE.LIMITE_KMH | Limite (km/h) | Decimal | Sim | Informado | Não | Interno | Maior que zero |
| CONFIGURACAO_LIMITE_VELOCIDADE.STATUS | Status | Enum | Sim | Informado | Não | Interno | Valores: `Ativa`/`Inativa` |

## Como este documento cresce

Mesmo princípio de todo o dicionário: um arquivo `NNN-categoria.md` por vez, na ordem do roadmap
(ver [`README.md`](./README.md)). Próximo, por D101: `docs/domain/009-app_motorista.md`, antes do
dicionário correspondente.
