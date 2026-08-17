# 007 — Fiscal

Atributos distintivos das 7 entidades de
[`../../domain/007-fiscal.md`](../../domain/007-fiscal.md). Atributos universais (D069), Padrões de
atributo/Atributos Críticos (D077/D081) e a regra de indicadores nunca operacionais (D090) não são
repetidos aqui — ver [`README.md`](./README.md). Máquinas de estado canônicas:
[`../../flows/009-FISCAL.md`](../../flows/009-FISCAL.md) (D035, com a máquina de CT-e expandida por
D106 nesta rodada).

Seis decisões atravessam todo este arquivo e não se repetem entidade por entidade: **D107** (XML/
certificado é evidência armazenada em `storage`, sempre `Arquivo`/`Referência`, nunca texto solto),
**D108** (toda integração externa é idempotente), **D109** (documento fiscal nunca é excluído
fisicamente, nem `Cancelado`/`Inutilizado`), **D111** (a chave de idempotência de cada integração é
sempre declarada explicitamente — nunca o UUID interno sozinho: CT-e/MDF-e → `PROTOCOLO_SEFAZ`;
CIOT → `PROTOCOLO_ANTT`/`CODIGO_CIOT`), **D112** (artefatos armazenados são versionados — `storage`
preserva todas as versões, a entidade referencia a mais recente), **D115** (toda integração externa
é observável — início, fim, duração, tentativa, resultado e origem, ver `Evento Fiscal`).

---

## CT-e

Dono: `documents` · Natureza: Transactional Data · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| CTE.VIAGEM_ID | Viagem | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| CTE.NUMERO | Número do CT-e | Texto Curto | Sim | Capturado (fornecido pela Configuração Fiscal do Tenant, D110) | Não | Interno | Nunca definido pelo próprio CT-e; nunca reutilizado (D084) |
| CTE.SERIE | Série | Texto Curto | Sim | Capturado (Configuração Fiscal do Tenant, D110) | Não | Interno | |
| CTE.CHAVE_ACESSO | Chave de acesso | Texto Curto | Não, obrigatório a partir de `TRANSMITIDO` | Capturado (gerada na transmissão) | Não | Interno | 44 dígitos; único nacionalmente (regra da SEFAZ, não apenas por tenant) |
| CTE.VALOR_SERVICO | Valor do serviço de transporte | Monetário | Sim | Capturado, no momento da transmissão | Não — imutável após `AUTORIZADO`; correção via cancelamento + reemissão | Financeiro | D097 — valor do frete declarado neste CT-e, moeda BRL (D075), no momento da transmissão à SEFAZ |
| CTE.STATUS | Status | Enum | Sim | Calculado (transições da máquina de estados, D106) | Sim, em `CTeStatusHistory` (D017/D018) | Interno | Valores: `RASCUNHO`/`VALIDADO`/`ASSINADO`/`TRANSMITIDO`/`AUTORIZADO`/`CANCELADO`/`DENEGADO`/`INUTILIZADO` — completo em `009-FISCAL.md`. **Atributo Crítico (D077)** — ver Governança abaixo |
| CTE.XML_ARQUIVO_ID | XML autorizado | Arquivo | Não, obrigatório em `AUTORIZADO` | Capturado (resposta da SEFAZ) | Não | Confidencial | D107 — referência ao artefato em `storage`, nunca o XML inline como texto |
| CTE.PROTOCOLO_SEFAZ | Protocolo de autorização/denegação | Texto Curto | Não, obrigatório a partir de `AUTORIZADO`/`DENEGADO` | Capturado (resposta da SEFAZ) | Não | Interno | **D111 — chave de idempotência declarada do CT-e**: uma resposta com o mesmo protocolo já processada é descartada, nunca gera segunda transição (D108) |
| CTE.DATA_HORA_AUTORIZACAO | Data/hora da autorização | Data/Hora | Não | Capturado (resposta da SEFAZ) | Não | Interno | Granularidade: segundo (D074) |

### Governança do atributo crítico `STATUS` (D077)

| Quem altera? | Quando muda? | Quem pode visualizar? | Quem nunca altera? |
|---|---|---|---|
| `documents`, a partir de eventos internos (validação, assinatura) e webhooks da SEFAZ (nunca manual, exceto solicitação de cancelamento pelo Faturista) | A cada transição válida da máquina de estados (`009-FISCAL.md`) | Conforme RBAC; Auditor sempre em leitura | Frontend (D027); Motorista, Gestor Operacional (apenas consultam — `freight` só lê o resumo via `VIAGEM.STATUS_FISCAL`) |

---

## MDF-e

Dono: `documents` · Natureza: Transactional Data · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| MDFE.VIAGEM_ID | Viagem | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| MDFE.CTE_IDS | CT-e consolidados | Referência (múltipla) | Sim, ao menos um | Capturado (sistema) | Não | Interno | N:N — um MDF-e pode consolidar vários CT-e `AUTORIZADO` da mesma viagem |
| MDFE.NUMERO | Número do MDF-e | Texto Curto | Sim | Capturado (Configuração Fiscal do Tenant, D110) | Não | Interno | Nunca reutilizado (D084) |
| MDFE.SERIE | Série | Texto Curto | Sim | Capturado (Configuração Fiscal do Tenant, D110) | Não | Interno | |
| MDFE.CHAVE_ACESSO | Chave de acesso | Texto Curto | Não, obrigatório a partir de `AUTORIZADO` | Capturado | Não | Interno | 44 dígitos |
| MDFE.STATUS | Status | Enum | Sim | Calculado | Sim, em `MDFeStatusHistory` | Interno | Valores: `PENDENTE`/`AUTORIZADO`/`ENCERRADO`/`CANCELADO`. **Atributo Crítico (D077)** — mesmo tratamento de `STATUS` do CT-e |
| MDFE.XML_ARQUIVO_ID | XML autorizado | Arquivo | Não, obrigatório em `AUTORIZADO` | Capturado | Não | Confidencial | D107 |
| MDFE.PROTOCOLO_SEFAZ | Protocolo | Texto Curto | Não | Capturado | Não | Interno | **D111 — chave de idempotência declarada** do MDF-e (D108) |
| MDFE.DATA_HORA_ENCERRAMENTO | Data/hora de encerramento | Data/Hora | Não | Capturado (sistema, ao concluir a última Entrega) | Não | Interno | Granularidade: segundo (D074) — dado bruto de origem para o indicador "tempo entre última entrega e encerramento" (calculado em `analytics`, D090) |

---

## CIOT

Dono: `documents` · Natureza: Transactional Data · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| CIOT.VIAGEM_ID | Viagem | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| CIOT.MOTORISTA_ID | Motorista autônomo | Referência | Sim | Capturado (sistema) | Não | Interno | FK — aplicável só quando `Motorista.TIPO_VINCULO = Autônomo` ([`001-cadastros.md`](./001-cadastros.md)) |
| CIOT.CODIGO_CIOT | Código CIOT | Texto Curto | Não, obrigatório a partir de `REGISTRADO` | Capturado (resposta da ANTT) | Não | Interno | Único nacionalmente; nunca reutilizado (D084) |
| CIOT.STATUS | Status | Enum | Sim | Calculado | Sim, em `CIOTStatusHistory` | Interno | Valores: `PENDENTE`/`REGISTRADO`/`CANCELADO` |
| CIOT.PROTOCOLO_ANTT | Protocolo | Texto Curto | Não | Capturado | Não | Interno | **D111 — chave de idempotência declarada** do CIOT (D108) |
| CIOT.DATA_HORA_REGISTRO | Data/hora do registro | Data/Hora | Não | Capturado | Não | Interno | Granularidade: segundo (D074) |

---

## Carta de Correção

Dono: `documents` · Natureza: Transactional Data · Histórica (D037/D083) · Parte do agregado CT-e.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| CARTA_CORRECAO.CTE_ID | CT-e | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável; só aceita CT-e em `AUTORIZADO` |
| CARTA_CORRECAO.NUMERO_SEQUENCIAL | Número sequencial | Inteiro | Sim | Calculado (sequencial por CT-e) | **É ela própria o histórico** — nunca editada (D037) | Interno | Nunca decresce para o mesmo CT-e |
| CARTA_CORRECAO.TEXTO_CORRECAO | Texto da correção | Texto Longo | Sim | Informado (Faturista) | Não | Interno | Só corrige erro formal — nunca valor ou partes envolvidas |
| CARTA_CORRECAO.XML_ARQUIVO_ID | XML da CC-e | Arquivo | Não | Capturado (resposta da SEFAZ) | Não | Confidencial | D107 |
| CARTA_CORRECAO.DATA_HORA_ENVIO | Data/hora do envio | Data/Hora | Sim | Capturado (sistema) | Não | Interno | Granularidade: segundo (D074) |

## NF-e Referenciada

Dono: `documents` · Natureza: Transactional Data · Parte do agregado CT-e.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| NFE_REFERENCIADA.CTE_ID | CT-e | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| NFE_REFERENCIADA.CHAVE_ACESSO | Chave de acesso da NF-e | Texto Curto | Sim | Informado (Cliente/embarcador) | Não | Interno | 44 dígitos; formato validado, sem confirmação de existência real na SEFAZ do emissor nesta fundação |
| NFE_REFERENCIADA.XML_ARQUIVO_ID | XML da NF-e | Arquivo | Não | Informado, quando fornecido pelo cliente | Não | Confidencial | D107 |

---

## Evento Fiscal

Dono: `documents` · Natureza: Transactional Data · **Time Series-like** (alto volume potencial) ·
Histórica (D037/D083) · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| EVENTO_FISCAL.DOCUMENTO_ID | Documento referenciado | Referência | Sim | Capturado (sistema) | Não | Interno | Aponta para CT-e, MDF-e ou CIOT |
| EVENTO_FISCAL.TIPO_DOCUMENTO | Tipo do documento | Enum | Sim | Capturado (sistema) | Não | Interno | Valores: `CTe`/`MDFe`/`CIOT` — resolve o polimorfismo de `DOCUMENTO_ID` |
| EVENTO_FISCAL.TIPO_EVENTO | Tipo de evento | Enum | Sim | Capturado (sistema) | **É ele próprio o histórico** (D037) | Interno | Valores: `Requisição`/`Resposta` |
| EVENTO_FISCAL.PAYLOAD_BRUTO | Payload bruto | Arquivo | Sim | Capturado (sistema, corpo da requisição/resposta) | Não | Confidencial | D107 — payload XML/JSON bruto armazenado em `storage`, referenciado por ID, nunca inline na entidade; versionado (D112) |
| EVENTO_FISCAL.PROTOCOLO_EXTERNO | Protocolo externo (chave de idempotência) | Texto Curto | Não | Capturado (SEFAZ/ANTT) | Não | Interno | **D111 — esta é a chave de idempotência declarada** para integrações fiscais: combinação `(DOCUMENTO_ID, PROTOCOLO_EXTERNO)` única, usada para descartar reprocessamento duplicado antes mesmo de interpretar o payload (D105/D108) |
| EVENTO_FISCAL.DATA_HORA_INICIO | Início da comunicação | Data/Hora | Sim | Capturado (sistema) | Não | Interno | Granularidade: segundo (D074). D115 — observabilidade |
| EVENTO_FISCAL.DATA_HORA_FIM | Fim da comunicação | Data/Hora | Não, obrigatório ao concluir | Capturado (sistema) | Não | Interno | Granularidade: segundo (D074). D115 |
| EVENTO_FISCAL.DURACAO_MS | Duração | Inteiro | Não | Calculado (`DATA_HORA_FIM − DATA_HORA_INICIO`) | Não | Interno | Milissegundos. D115 — dado bruto para monitoramento, o indicador agregado (latência média) é de `analytics` (D090) |
| EVENTO_FISCAL.NUMERO_TENTATIVA | Número da tentativa | Inteiro | Sim | Capturado (sistema) | Não | Interno | 1 para a primeira chamada; incrementado a cada retry. D115 |
| EVENTO_FISCAL.RESULTADO | Resultado | Enum | Não, obrigatório ao concluir | Capturado (sistema) | Não | Interno | Valores: `Sucesso`/`Falha`/`Timeout`. D115 |
| EVENTO_FISCAL.ORIGEM | Origem da chamada | Enum | Sim | Capturado (sistema) | Não | Interno | Valores: `documents` (emissão automática)/Faturista (ação manual, ex: reenvio). D115 |

---

## Configuração Fiscal do Tenant

Dono: `documents` · Natureza: Reference Data (D036) · Aggregate Root · Dados Permanentes (D078,
salvo o certificado, que tem validade).

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| CONFIGURACAO_FISCAL.CERTIFICADO_ARQUIVO_ID | Certificado digital | Arquivo | Sim | Informado | Sim (troca de certificado gera novo registro auditado) | Confidencial, Crítico | D107 — referência ao artefato em `storage`, nunca o certificado inline |
| CONFIGURACAO_FISCAL.CERTIFICADO_VALIDADE | Validade do certificado | Data | Sim | Informado/Capturado (do próprio certificado) | Não | Interno | Granularidade: dia (D074); gatilho de alerta de expiração |
| CONFIGURACAO_FISCAL.AMBIENTE | Ambiente | Enum | Sim | Informado | Não | Interno | Valores: `Produção`/`Homologação` |
| CONFIGURACAO_FISCAL.REGIME_TRIBUTARIO | Regime tributário | Enum | Sim | Informado | Não | Interno | |
| CONFIGURACAO_FISCAL.SERIE_CTE | Série ativa de CT-e | Texto Curto | Sim | Informado | Não | Interno | D110 — CT-e nunca define sua própria série |
| CONFIGURACAO_FISCAL.PROXIMO_NUMERO_CTE | Próximo número de CT-e | Inteiro | Sim | Calculado (incrementado a cada emissão) | Não — é o próprio contador | Interno | D110 — única fonte de numeração; nunca decresce nem é reutilizado (D084) |
| CONFIGURACAO_FISCAL.SERIE_MDFE | Série ativa de MDF-e | Texto Curto | Sim | Informado | Não | Interno | D110 |
| CONFIGURACAO_FISCAL.PROXIMO_NUMERO_MDFE | Próximo número de MDF-e | Inteiro | Sim | Calculado | Não — é o próprio contador | Interno | D110, D084 |
| CONFIGURACAO_FISCAL.STATUS | Status | Enum | Sim | Calculado (validade do certificado) | Sim | Interno | Valores: `Ativa`/`Expirada`/`Inativa` |

## Como este documento cresce

Mesmo princípio de todo o dicionário: um arquivo `NNN-categoria.md` por vez, na ordem do roadmap
(ver [`README.md`](./README.md)). Próximo, por D101: `docs/domain/008-rastreamento.md`, antes do
dicionário correspondente.
