# 007 — Fiscal

Entidades do ciclo de documentos fiscais do GestorFrete (CT-e, MDF-e, CIOT e correlatas). Template
completo de 22 campos (ver [`README.md`](./README.md)). Máquinas de estado canônicas:
[`../flows/009-FISCAL.md`](../flows/009-FISCAL.md) (D035). Lista reconciliada (D076) contra
`ENTITY_CATALOG.md`: as 7 entidades abaixo já batiam integralmente com o placeholder original — sem
divergência a registrar desta vez.

Nenhuma destas entidades duplica `VIAGEM.STATUS_FISCAL` ([`002-operacao.md`](../database/dictionary/002-operacao.md))
— aquele campo é a **projeção resumida** que a Viagem mantém (D081), escrita pelo próprio agregado
Viagem ao consumir eventos publicados por `documents` (D064); os detalhes completos de cada
documento fiscal individual vivem exclusivamente aqui, de posse de `documents` (D033/D034).

---

## CT-e

- **Objetivo**: Representa o Conhecimento de Transporte Eletrônico de uma Viagem — o documento
  fiscal que formaliza a prestação do serviço de transporte perante a SEFAZ.
- **Responsabilidades**: Orquestrar emissão, autorização, denegação e cancelamento junto à SEFAZ;
  habilitar o Faturamento (`financial`) e o MDF-e.
- **O que não faz**: Não é emitido pela transportadora sem uma Viagem despachada; não substitui a
  NF-e do embarcador (apenas a referencia).
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `documents`
- **Principais relacionamentos**: Viagem (referenciada, N:1); NF-e Referenciada (1:N); Carta de
  Correção (1:N, filha do agregado); MDF-e (N:1, quando consolidado).
- **Eventos que publica**: `CTeEmitido`, `CTeCancelado`, `CTeDenegado`, `CTeCorrigido` (já
  catalogados em [`../product/EVENT_MAP.md`](../product/EVENT_MAP.md)).
- **Eventos que consome**: `ViagemDespachada` (`freight`) — dispara a emissão.
- **Invariantes**: um CT-e `CANCELADO` nunca retorna a `AUTORIZADO`; cancelamento só dentro do prazo
  legal.
- **Regras de negócio associadas**: D015–D018 (máquina de estados + histórico), D019/D020 (uma das
  três dimensões que convergem para `ENCERRADA`), D106 (máquina de estados própria, mais granular
  que o `STATUS_FISCAL` resumido da Viagem), D108 (idempotência ao processar resposta da SEFAZ),
  D109 (nunca excluído fisicamente), D110 (número/série vêm da Configuração Fiscal do Tenant, nunca
  definidos pelo próprio CT-e).
- **Estados**: `RASCUNHO` / `VALIDADO` / `ASSINADO` / `TRANSMITIDO` / `AUTORIZADO` / `CANCELADO` /
  `DENEGADO` / `INUTILIZADO` — máquina completa em `009-FISCAL.md` (D106); a Viagem só enxerga o
  resumo `PENDENTE`/`AUTORIZADO`/`CANCELADO`/`DENEGADO` (D081, projeção).
- **Auditoria**: D007, motivo obrigatório em `CANCELADO`/`DENEGADO`/`INUTILIZADO`.
- **Linha do tempo (Timeline Universal)**: funde-se à da Viagem (D022); por D114, inclui não só as
  transições de `CTeStatusHistory`, mas também eventos de acesso/uso (download do XML, download do
  PDF/DACTE, Carta de Correção anexada) — relevante para suporte, não apenas para o negócio.
- **Anexos suportados**: XML e PDF (DACTE) — por D107, são evidência armazenada em `storage`,
  referenciada por ID, nunca um campo próprio do CT-e; versionados (D112, uma reemissão de PDF não
  apaga a anterior); obrigatórios por compliance (D024).
- **Comentários suportados**: Sim, tratativa de denegação/cancelamento (D023).
- **KPIs relacionados**: tempo médio de emissão, percentual de documentos denegados (indicadores em
  `analytics`, D090 — aqui só o dado bruto).
- **Documentos canônicos relacionados**: `009-FISCAL.md`.
- **Evoluções futuras previstas**: emissão em modo de contingência quando a SEFAZ estiver
  indisponível.
- **Dependências obrigatórias**: Viagem.
- **Dependências proibidas**: Cliente diretamente (acessa via Viagem), Ordem de Serviço, Pneu.
- **Dono da Timeline**: Aggregate Viagem (o CT-e contribui à timeline da Viagem, não tem timeline
  isolada).
- **Capacidade Offline**: Não (D039) — emissão exige conectividade com a SEFAZ.

## MDF-e

- **Objetivo**: Representa o Manifesto Eletrônico de Documentos Fiscais, consolidando um ou mais
  CT-e de uma mesma Viagem.
- **Responsabilidades**: Orquestrar emissão e encerramento junto à SEFAZ; seu encerramento é uma das
  três condições de `ENCERRADA` (D019).
- **O que não faz**: Não é emitido sem ao menos um CT-e `AUTORIZADO`; não decide sozinho quando
  encerrar — depende da conclusão operacional da última Entrega (evento consumido).
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `documents`
- **Principais relacionamentos**: Viagem (referenciada, N:1); CT-e (N:N — um MDF-e consolida vários
  CT-e da mesma viagem, no fluxo multi-cliente/multi-carga).
- **Eventos que publica**: `MDFeEmitido`, `MDFeEncerrado`, `MDFeCancelado` (já catalogados).
- **Eventos que consome**: `EntregaRealizada` (última da viagem, `freight`) — dispara o
  encerramento.
- **Invariantes**: não emite sem CT-e `AUTORIZADO` vinculado; não encerra antes da conclusão
  operacional da última Entrega; não cancela após `ENCERRADO`; nunca excluído fisicamente, mesmo
  `CANCELADO` (D109).
- **Regras de negócio associadas**: D015–D018, D019/D020, D108 (idempotência), D109 (nunca
  excluído), D110 (número/série da Configuração Fiscal do Tenant).
- **Estados**: `PENDENTE` / `AUTORIZADO` / `ENCERRADO` / `CANCELADO`.
- **Auditoria**: D007, motivo obrigatório em `CANCELADO`.
- **Linha do tempo**: funde-se à da Viagem.
- **Anexos suportados**: XML e PDF (DAMDFE) (D024).
- **Comentários suportados**: Sim (D023).
- **KPIs relacionados**: tempo entre última entrega e encerramento (mesmo indicador citado como
  risco em `009-FISCAL.md` — dado bruto aqui, cálculo em `analytics`, D090).
- **Documentos canônicos relacionados**: `009-FISCAL.md`.
- **Evoluções futuras previstas**: alerta automático de prazo de encerramento próximo do limite.
- **Dependências obrigatórias**: Viagem, ao menos um CT-e `AUTORIZADO`.
- **Dependências proibidas**: Cliente diretamente, Ordem de Serviço, Pneu.
- **Dono da Timeline**: Aggregate Viagem.
- **Capacidade Offline**: Não.

## CIOT

- **Objetivo**: Representa o Código Identificador da Operação de Transporte, obrigatório quando a
  Viagem envolve motorista autônomo (TAC).
- **Responsabilidades**: Registrar a operação junto à ANTT antes do início da viagem.
- **O que não faz**: Não se aplica a motoristas empregados (`Motorista.TIPO_VINCULO = Empregado`,
  [`001-cadastros.md`](./001-cadastros.md)).
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `documents`
- **Principais relacionamentos**: Viagem (referenciada, N:1); Motorista (referenciado, autônomo).
- **Eventos que publica**: `CIOTRegistrado`, `CIOTCancelado` (já catalogados).
- **Eventos que consome**: Nenhum.
- **Invariantes**: aplicável apenas quando `Motorista.TIPO_VINCULO = Autônomo`; cancelamento só
  antes do início da viagem; nunca excluído fisicamente, mesmo `CANCELADO` (D109).
- **Regras de negócio associadas**: D015–D018, D109.
- **Estados**: `PENDENTE` / `REGISTRADO` / `CANCELADO`.
- **Auditoria**: D007.
- **Linha do tempo**: funde-se à da Viagem.
- **Anexos suportados**: comprovante de registro ANTT (D024).
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: `009-FISCAL.md`.
- **Evoluções futuras previstas**: Nenhuma prevista.
- **Dependências obrigatórias**: Viagem, Motorista autônomo.
- **Dependências proibidas**: Cliente diretamente, Ordem de Serviço, Pneu.
- **Dono da Timeline**: Aggregate Viagem.
- **Capacidade Offline**: Não.

## Carta de Correção

- **Objetivo**: Registro histórico (D037) de correção de erro formal em um CT-e já `AUTORIZADO` (ex:
  erro de digitação em observações) — não altera valores fiscais nem partes envolvidas.
- **Responsabilidades**: Guardar o texto da correção e a data de envio à SEFAZ.
- **O que não faz**: Não é uma transição de status do CT-e — o CT-e permanece `AUTORIZADO`; não
  corrige erros que alterem valores/partes (esses exigem cancelamento e reemissão).
- **Aggregate Root**: Não — parte do agregado CT-e; entidade **Histórica** (D037).
- **Bounded Context proprietário**: `documents`
- **Principais relacionamentos**: CT-e (N:1).
- **Eventos que publica**: Nenhum diretamente — refletido por `CTeCorrigido`.
- **Eventos que consome**: Nenhum.
- **Invariantes**: só é anexada a um CT-e `AUTORIZADO`; nunca editada após enviada (D037).
- **Regras de negócio associadas**: D017/D018/D037.
- **Estados**: Não aplicável — registro pontual, imutável.
- **Auditoria**: D007.
- **Linha do tempo**: parte do CT-e/Viagem.
- **Anexos suportados**: XML da CC-e (D024).
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: quantidade de Cartas de Correção emitidas (indicador de qualidade de
  cadastro, calculado em `analytics`, D090).
- **Documentos canônicos relacionados**: `009-FISCAL.md`.
- **Evoluções futuras previstas**: Nenhuma isolada.
- **Dependências obrigatórias**: CT-e.
- **Dependências proibidas**: Cliente diretamente, Ordem de Serviço, Pneu, Financeiro.
- **Dono da Timeline**: Aggregate Viagem (via CT-e).
- **Capacidade Offline**: Não.

## NF-e Referenciada

- **Objetivo**: Representa a referência a uma Nota Fiscal Eletrônica do Cliente/embarcador que
  acompanha a carga — o GestorFrete nunca emite NF-e, apenas a referencia no CT-e.
- **Responsabilidades**: Guardar chave de acesso e dados mínimos da NF-e para composição do CT-e.
- **O que não faz**: Não é emitida, validada ou alterada pelo GestorFrete — é um dado informado,
  cuja veracidade é de responsabilidade do Cliente/embarcador.
- **Aggregate Root**: Não — parte do agregado CT-e.
- **Bounded Context proprietário**: `documents`
- **Principais relacionamentos**: CT-e (N:1).
- **Eventos que publica**: Nenhum.
- **Eventos que consome**: Nenhum.
- **Invariantes**: chave de acesso com formato válido (44 dígitos), mas sem validação de existência
  real junto à SEFAZ nesta fundação.
- **Regras de negócio associadas**: D005/D006.
- **Estados**: Não aplicável.
- **Auditoria**: D007.
- **Linha do tempo**: parte do CT-e.
- **Anexos suportados**: XML da NF-e, quando fornecido pelo cliente (D024).
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: `009-FISCAL.md`.
- **Evoluções futuras previstas**: validação de existência via integração com a SEFAZ do emissor.
- **Dependências obrigatórias**: CT-e.
- **Dependências proibidas**: Cliente diretamente (é informativa, não pertence ao cadastro de
  Cliente), Ordem de Serviço, Pneu, Financeiro.
- **Dono da Timeline**: Aggregate Viagem (via CT-e).
- **Capacidade Offline**: Não.

## Evento Fiscal

- **Objetivo**: Registro histórico (D037) bruto de cada comunicação com a SEFAZ/ANTT (requisição e
  resposta), independente de ela ter resultado numa transição de status — a matéria-prima de
  auditoria e depuração de integração fiscal.
- **Responsabilidades**: Guardar payload bruto enviado/recebido, timestamp, e a qual documento
  (CT-e/MDF-e/CIOT) se refere.
- **O que não faz**: Não substitui `CTeStatusHistory`/`MDFeStatusHistory`/`CIOTStatusHistory` (D017/
  D018, já parte de cada aggregate) — aqueles são a interpretação de negócio da transição; este é o
  log técnico bruto da comunicação, útil para suporte e compliance quando a SEFAZ reporta algo que
  não mapeia diretamente para uma transição esperada (ex: erro de schema, timeout).
- **Aggregate Root**: Sim — entidade **Histórica** (D037), independente por natureza (pode existir
  mesmo sem gerar transição de status).
- **Bounded Context proprietário**: `documents`
- **Principais relacionamentos**: CT-e, MDF-e ou CIOT (referenciado, exatamente um).
- **Eventos que publica**: Nenhum diretamente.
- **Eventos que consome**: Nenhum — é o próprio registro da comunicação externa, não reage a
  eventos internos.
- **Invariantes**: nunca editado após inserido (D037); nunca apagado, mesmo inválido, duplicado ou
  rejeitado (D113 — é evidência de comunicação, independente do resultado); processado de forma
  idempotente — a mesma resposta recebida mais de uma vez (reentrega/retry) nunca gera dois Eventos
  Fiscais equivalentes nem duas transições de status do documento referenciado (D105/D108/D111).
- **Regras de negócio associadas**: D017/D018/D037, D007, D105 (evento técnico não altera domínio
  diretamente — precisa ser interpretado pelas regras de `documents`), D108/D111 (idempotência via
  chave declarada — `PROTOCOLO_EXTERNO`), D113 (nunca apagado), D115 (observabilidade — início,
  fim, duração, tentativa, resultado, origem).
- **Estados**: Não aplicável.
- **Auditoria**: D007 — este é, ele mesmo, um artefato de auditoria fiscal.
- **Linha do tempo**: não aparece diretamente na Timeline Universal do usuário (é técnico) — apenas
  consultável por Suporte/Auditor.
- **Anexos suportados**: Não aplicável (o payload já é o próprio conteúdo).
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: `009-FISCAL.md`.
- **Evoluções futuras previstas**: alimentar IA de diagnóstico de falhas de integração fiscal
  recorrentes.
- **Dependências obrigatórias**: CT-e, MDF-e ou CIOT.
- **Dependências proibidas**: Cliente, Ordem de Serviço, Pneu, Financeiro.
- **Dono da Timeline**: Aggregate Viagem (via o documento referenciado), embora não exibido na
  timeline de negócio (só na técnica/suporte).
- **Capacidade Offline**: Não.

## Configuração Fiscal do Tenant

- **Objetivo**: Guarda os parâmetros fiscais necessários para o tenant emitir documentos (certificado
  digital, ambiente SEFAZ, série de numeração, regime tributário).
- **Responsabilidades**: Ser consultada antes de qualquer emissão de CT-e/MDF-e/CIOT; **dona
  exclusiva da numeração/série de cada tipo de documento fiscal (D110)** — fornece o próximo número
  disponível quando um CT-e/MDF-e entra em `RASCUNHO`; nenhum documento define ou guarda sua própria
  lógica de sequenciamento.
- **O que não faz**: Não emite documento sozinha — apenas fornece os parâmetros e a numeração que a
  emissão usa.
- **Aggregate Root**: Sim — entidade de **Referência** (D036), um registro por tenant.
- **Bounded Context proprietário**: `documents`
- **Principais relacionamentos**: Nenhum — é configuração de nível de tenant, sem relacionamento
  com entidades transacionais (referenciada por elas, nunca o contrário).
- **Eventos que publica**: `ConfiguracaoFiscalAtualizada` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: um único registro `Ativo` por tenant; certificado digital com validade (alerta de
  expiração, análogo a Documento do Veículo, [`003-frota.md`](./003-frota.md)); numeração
  estritamente sequencial e nunca reutilizada por tipo de documento/série (D084 aplicado à
  numeração fiscal).
- **Regras de negócio associadas**: D005/D006, D007, D110 (dona exclusiva da numeração/série).
- **Estados**: `Ativa` / `Expirada` (do certificado) / `Inativa`.
- **Auditoria**: D007 — alteração de certificado/ambiente é sensível o suficiente para exigir
  auditoria reforçada.
- **Linha do tempo**: própria, alterações de configuração.
- **Anexos suportados**: certificado digital (arquivo, D024) — classificado como Confidencial/
  Crítico.
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: `009-FISCAL.md`.
- **Evoluções futuras previstas**: alerta automático de expiração do certificado digital.
- **Dependências obrigatórias**: Nenhuma.
- **Dependências proibidas**: Cliente, Viagem, Ordem de Serviço, Pneu, Financeiro (é lida por eles
  indiretamente via `documents`, nunca o contrário).
- **Dono da Timeline**: Aggregate Configuração Fiscal do Tenant (este próprio).
- **Capacidade Offline**: Não.
