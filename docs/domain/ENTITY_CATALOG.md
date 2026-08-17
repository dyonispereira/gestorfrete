# ENTITY_CATALOG.md — Índice de Entidades

Índice de todas as entidades de negócio do GestorFrete, organizadas pela mesma categoria do
arquivo de detalhe em que cada uma será documentada (`NNN-categoria.md`, ver
[`README.md`](./README.md)). Apenas nomes aqui — nenhuma descrição, nenhuma regra. Isso
é deliberado: o catálogo existe para navegação rápida em um modelo que ficará grande demais para um
único documento, não para explicar nada.

Cada entidade é detalhada, com o template oficial (ver
[`README.md`](./README.md)), no arquivo numerado correspondente, quando esse arquivo for
escrito — este índice é atualizado (status e eventuais entidades novas descobertas durante a
escrita) a cada arquivo concluído, nunca fica desatualizado.

## 001 — Cadastros

- Cliente
- Contato do Cliente
- Fornecedor
- Motorista
- Funcionário
- Seguradora
- Filial
- Centro de Custo
- Tabela de Preço
- Item de Tabela de Preço
- Usuário
- Papel
- Permissão
- Rota Padrão
- Trecho de Rota
- Praça de Pedágio
- Endereço (nova, D182 — identificada ao modelar a camada relacional, `relational/002-cadastros.md`)
- Documento do Motorista (nova, D183 — idem)

## 002 — Operação

- Viagem
- Entrega
- Coleta
- Ocorrência
- Romaneio
- Item de Carga
- Canhoto
- Contrato de Frete
- Cotação
- Item de Cotação
- Solicitação de Frete
- Janela de Entrega
- Ponto de Parada da Viagem
- Alocação de Recurso da Viagem

## 003 — Frota

- Veículo Tracionador
- Implemento
- Composição Veicular
- Ficha Técnica do Veículo
- Documento do Veículo
- Apólice de Seguro Veicular
- Leitura de Hodômetro
- Licenciamento do Veículo
- Categoria de Veículo
- Disponibilidade do Veículo

## 004 — Manutenção

- Ordem de Serviço
- Item de Ordem de Serviço
- Solicitação de Peça
- Peça em Estoque
- Movimentação de Estoque
- Plano de Manutenção Preventiva
- Tipo de Serviço
- Aprovação de Custo

## 005 — Pneus

- Pneu
- Registro de Recapagem
- Posicionamento de Pneu
- Modelo de Pneu
- Política de Recapagem

## 006 — Financeiro

Lista original (placeholder, antes de `006-financeiro.md` ser escrito) reconciliada (D076) contra o
que de fato existe — diferenças documentadas, não silenciadas:

- **Fatura**, **Conta a Receber**, **Conta a Pagar**, **Conciliação Bancária** — confirmadas.
- **Rateio de Custo** → renomeada **Rateio de Despesa** (nome mais preciso: rateia despesas, não
  "custo" em abstrato).
- **Adiantamento**, **Haver** → **não são entidades de `financial`** — pertencem ao bounded context
  `drivers` (adiantamento ao motorista); `006-financeiro.md` as referencia apenas como ponto de
  integração, sem recriá-las (D033/D034).
- **Lançamento de Centro de Custo** → não existe como entidade própria; Centro de Custo já é
  cadastro em `001-cadastros.md`, referenciado diretamente por **Rateio de Despesa**.
- **Valor Previsto da Viagem**, **Valor Realizado da Viagem** → não são entidades; já são atributos
  da própria Viagem (`RECEITA_PREVISTA_SNAPSHOT`, `CUSTO_PREVISTO`, etc.) em
  [`002-operacao.md`](./002-operacao.md), D086.
- **Fluxo de Caixa**, **DRE** → não modelados como entidade — são indicadores agregados de
  `analytics`/BI (D090), nunca atributos/entidades do domínio operacional. Em vez disso,
  **Posição de Caixa** foi criada como read model operacional (saldo projetado do dia a dia,
  distinto do Fluxo de Caixa/DRE consolidado).
- Novas, identificadas durante a escrita: **Aprovação de Despesa**, **Lançamento de Extrato
  Bancário**, **Estorno Financeiro**, **Forma de Pagamento**, **Plano de Contas**.

Lista final (11 entidades):

- Fatura
- Conta a Receber
- Conta a Pagar
- Aprovação de Despesa
- Rateio de Despesa
- Lançamento de Extrato Bancário
- Conciliação Bancária
- Estorno Financeiro
- Forma de Pagamento
- Plano de Contas
- Posição de Caixa

## 007 — Fiscal

- CT-e
- MDF-e
- CIOT
- Carta de Correção
- NF-e Referenciada
- Evento Fiscal
- Configuração Fiscal do Tenant

## 008 — Rastreamento

Lista original (placeholder) reconciliada (D076) — ver `008-rastreamento.md` para o raciocínio
completo: `Parada de Veículo`/`Desvio de Rota`/`Evento de Velocidade` consolidadas em **Evento de
Rastreamento** (um `TIPO` fechado, não uma entidade por tipo, mesmo princípio de `Ocorrência` em
`002-operacao.md`); `Geofence` mantida com nome de negócio dual "Cerca Eletrônica" (D028); duas
entidades novas exigidas pelo requisito de agnosticismo de fornecedor (**Provedor de
Rastreamento**, **Equipamento de Rastreamento**) e uma pela separação explícita Posição × Telemetria
(**Leitura de Telemetria**).

Lista final (9 entidades):

- Provedor de Rastreamento
- Equipamento de Rastreamento
- Origem de Localização
- Posição de Veículo
- Leitura de Telemetria
- Heartbeat
- Cerca Eletrônica (Geofence)
- Evento de Rastreamento
- Configuração de Limite de Velocidade

## 009 — App (Motorista)

Lista original (placeholder) reconciliada (D076) — ver `009-app_motorista.md`: `Indicador de
Desempenho do Motorista` e `Configuração de Ranking Interno` **removidas** (violavam D090 —
indicador agregado/ranking nunca é entidade do domínio operacional, é cálculo de `analytics`);
`Item Pendente de Sincronização` renomeada **Fila de Sincronização`; nova entidade **Dispositivo
Mobile** (persistente, distinta de Sessão Mobile, que é transiente).

Lista final (5 entidades):

- Sessão Mobile
- Dispositivo Mobile
- Fila de Sincronização
- Registro de Sincronização
- Assinatura Digital

## 010 — Administração (Plataforma)

Lista original (placeholder) reconciliada (D076) — ver `010-administracao.md` para o raciocínio
completo. `Tenant`/`Assinatura`/`Plano`/`Item de Plano`/`Cobrança Recorrente` confirmados;
`Configuração do Tenant` (genérico) desdobrado em três entidades específicas (Configuração
Regional, Configuração de Numeração, Parâmetro do Tenant), conforme a estrutura em 6 blocos pedida
nesta rodada exigiu granularidade maior; `Atribuição de Consultor Comercial`/`Ticket de Suporte`/
`Interação do Ticket` **adiadas** (pertencem a `support`, fora dos 6 blocos pedidos — não removidas,
apenas não cobertas neste lote). 14 entidades novas identificadas a partir dos 6 blocos (Identidade,
Segurança, Configurações, Personalização, Administração da Plataforma).

Lista final (22 entidades — 20 originais + 2 adicionadas no Sprint 10/Lote 12, D323, quando a
auditoria da API encontrou `notification_center.alert.*` já em `RBAC_MATRIX.md` sem entidade
correspondente):

- Tenant
- Plano
- Item de Plano
- Assinatura
- Cobrança Recorrente
- Grupo de Usuários
- Convite
- Fator de Autenticação
- Sessão de Acesso
- Token de API
- Bloqueio de Acesso
- Log de Auditoria
- Configuração Regional do Tenant
- Configuração de Numeração
- Parâmetro do Tenant
- Configuração de Personalização
- Recurso Habilitado do Tenant
- Configuração de Integração
- Webhook
- Execução de Job
- Notificação (D323, Sprint 10/Lote 12)
- Preferência de Canal de Notificação (D323, Sprint 10/Lote 12)

## 011 — BI

Lista original confirmada integralmente (D076 — nenhuma renomeação/remoção), mais 4 entidades
novas exigidas pelos conceitos desta rodada (`Métrica` é o mesmo conceito pedido como "Catálogo de
Indicadores" — uma só entidade, não duas):

- Métrica
- Indicador Consolidado
- Snapshot Analítico
- Cubo Analítico
- Dashboard Personalizado
- Filtro Favorito
- Relatório Salvo
- Exportação Gerada
- Agendamento de Atualização

## 012 — IA

Lista original reconciliada (D076): `Sugestão de IA`, `Anomalia Detectada`, `Modelo de IA`
confirmadas; `Previsão de IA` renomeada **Predição de IA** (consistência com "Predição de
Manutenção Preventiva" já usada em `004-manutencao.md`). 4 novas — `Inferência de IA` (registro
técnico de execução, distinto do resultado de negócio, D105), `Classificação de IA` (Risco/
Prioridade/Gravidade consolidados em um `TIPO_CLASSIFICACAO`), `Leitura por Visão Computacional`
(OCR/canhotos/avarias/pneus/implementos) e `Feedback de IA` (D165). Nenhuma entidade por área
funcional pedida (Otimização, por exemplo, é só uma `CATEGORIA` de `Sugestão de IA`) — teria gerado
15+ entidades quase idênticas.

Lista final (8 entidades):

- Modelo de IA
- Inferência de IA
- Sugestão de IA
- Predição de IA
- Classificação de IA
- Anomalia Detectada
- Leitura por Visão Computacional
- Feedback de IA

---

## Contagem

177 entidades catalogadas (104 + 11 de `006-financeiro.md` + 7 de
`007-fiscal.md` + 9 de `008-rastreamento.md` + 5 de `009-app_motorista.md` + 22 de
`010-administracao.md` + 9 de `011-bi.md` + 8 de `012-ia.md` + 2 de `001-cadastros.md`, Endereço e
Documento do Motorista, adicionadas durante a modelagem relacional, D102/D182/D183), dentro da faixa
esperada de 120-180 (levemente acima, consequência honesta do domínio real, não forçada). O número
pode ainda crescer durante a etapa de modelagem física, se algum atributo revelar a necessidade de
uma entidade nova (D102 — nasce primeiro aqui, nunca direto no dicionário). Última atualização:
Sprint 10/Lote 12 (D323, `010-administracao.md` 20 → 22 — Notificação/Preferência de Canal de
Notificação, gap entre RBAC e Domain fechado durante a auditoria da API). Este número não é um
alvo a ser forçado — é uma consequência do domínio real, revisada a cada lote.
