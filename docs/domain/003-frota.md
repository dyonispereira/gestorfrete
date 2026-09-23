# 003 — Frota

Entidades da frota (veículos e implementos) do GestorFrete. Primeiro arquivo com o template
completo de 22 campos (ver [`README.md`](./README.md)) — inclui Dependências obrigatórias,
Dependências proibidas, Dono da Timeline e Capacidade Offline. Ver
[`ENTITY_CATALOG.md`](./ENTITY_CATALOG.md) para o índice completo desta categoria.

---

## Veículo Tracionador

- **Objetivo**: Representa o cavalo mecânico (unidade motora) da frota ou agregado.
- **Responsabilidades**: Executar viagens; receber despesas (por referência); possuir documentos;
  receber manutenções; receber pneus; receber checklists; gerar indicadores.
- **O que não faz**: Não é responsável pelo financeiro da empresa; não emite CT-e (isso é
  `documents`).
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `fleet`
- **Principais relacionamentos**: Motorista, Implemento, Viagem (referenciados por ID); Ficha
  Técnica do Veículo, Documento do Veículo, Apólice de Seguro Veicular, Leitura de Hodômetro
  (filhos do agregado).
- **Eventos que publica**: `VeiculoCadastrado`, `VeiculoInativado` (novos).
- **Eventos que consome**: `PneuInstalado`, `OrdemServicoAberta`, `OrdemServicoConcluida` (já
  catalogados — refletem na Disponibilidade do Veículo).
- **Invariantes**: placa única por tenant; veículo `Inativo` não pode ser alocado a nova Viagem.
- **Regras de negócio associadas**: D001, D005/D006, D029/D030 (placa não é o código funcional —
  é um Value Object próprio, ver `shared/VALUE_OBJECTS.md`, a ser escrito).
- **Estados**: Ver Disponibilidade do Veículo, abaixo — o próprio Veículo Tracionador tem apenas
  `Ativo`/`Inativo` (D001); a disponibilidade operacional é derivada, não armazenada aqui.
- **Auditoria**: D007.
- **Linha do tempo (Timeline Universal)**: cadastro, viagens, manutenções, trocas de pneu —
  agregando eventos de outros aggregates por referência (D022).
- **Anexos suportados**: CRLV, foto do veículo (D024).
- **Comentários suportados**: Sim (D023).
- **KPIs relacionados**: disponibilidade da frota, custo por km.
- **Documentos canônicos relacionados**: referenciado por
  [`../flows/002-VIAGEM.md`](../flows/002-VIAGEM.md), [`../flows/003-MANUTENCAO.md`](../flows/003-MANUTENCAO.md)
  e [`../flows/004-PNEUS.md`](../flows/004-PNEUS.md) — nenhum fluxo de negócio dedicado ainda.
- **Evoluções futuras previstas**: telemetria embarcada.
- **Dependências obrigatórias**: Filial (opcional, mas comum), Categoria de Veículo.
- **Dependências proibidas**: Financeiro, CT-e, Cliente (D033/D034 — não importa nada desses
  bounded contexts).
- **Dono da Timeline**: Aggregate Veículo Tracionador (este próprio).
- **Capacidade Offline**: Consulta Offline (D039) — o app do motorista precisa consultar dados do
  veículo mesmo sem conexão, mas não os edita offline.

## Implemento

- **Objetivo**: Representa a carreta/semirreboque/reboque acoplado ao cavalo mecânico.
- **Responsabilidades**: Ser acoplado a um Veículo Tracionador numa Viagem; possuir documentos
  próprios.
- **O que não faz**: Não se move sozinho — depende de um Veículo Tracionador.
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `fleet`
- **Principais relacionamentos**: Composição Veicular (N:1, quando parte de bitrem/rodotrem);
  Viagem (referenciada).
- **Eventos que publica**: `ImplementoCadastrado` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: placa única por tenant.
- **Regras de negócio associadas**: D001, D005/D006.
- **Estados**: `Disponível` / `Em Uso` / `Inativo`.
- **Auditoria**: D007.
- **Linha do tempo**: cadastro, uso em viagens.
- **Anexos suportados**: CRLV (D024).
- **Comentários suportados**: Sim (D023).
- **KPIs relacionados**: utilização por implemento.
- **Documentos canônicos relacionados**: Nenhum.
- **Evoluções futuras previstas**: rastreamento próprio de implemento (hoje herda do veículo
  tracionador).
- **Dependências obrigatórias**: Categoria de Veículo.
- **Dependências proibidas**: Financeiro, CT-e, Cliente, Motorista (implemento não tem motorista
  próprio).
- **Dono da Timeline**: Aggregate Implemento (este próprio).
- **Capacidade Offline**: Consulta Offline.

## Composição Veicular

- **Objetivo**: Registra a combinação específica de Veículo Tracionador + Implemento(s) usada em
  uma configuração (bitrem/rodotrem — ver [`../product/GLOSSARY.md`](../product/GLOSSARY.md)).
- **Responsabilidades**: Validar limites regulatórios (CONTRAN) da combinação.
- **O que não faz**: Não substitui o cadastro individual de cada Veículo/Implemento.
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `fleet`
- **Principais relacionamentos**: Veículo Tracionador (N:1); Implemento (N:N).
- **Eventos que publica**: `ComposicaoVeicularValidada` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: número de eixos e comprimento total dentro dos limites do CONTRAN.
- **Regras de negócio associadas**: D001, D005/D006.
- **Estados**: `Válida` / `Inválida`.
- **Auditoria**: D007.
- **Linha do tempo**: criação, validações.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: Nenhum.
- **Evoluções futuras previstas**: validação automática por regra regulatória.
- **Dependências obrigatórias**: Veículo Tracionador, Implemento.
- **Dependências proibidas**: Financeiro, CT-e, Cliente, Motorista.
- **Dono da Timeline**: Aggregate Composição Veicular (este próprio).
- **Capacidade Offline**: Não.

## Ficha Técnica do Veículo

- **Objetivo**: Dados técnicos detalhados do veículo (motor, capacidade de carga, ano, chassi).
- **Responsabilidades**: Guardar especificações técnicas fixas do veículo.
- **O que não faz**: Não guarda dados operacionais — isso é Leitura de Hodômetro/Disponibilidade
  do Veículo.
- **Aggregate Root**: Não — parte do agregado Veículo Tracionador.
- **Bounded Context proprietário**: `fleet`
- **Principais relacionamentos**: Veículo Tracionador (1:1).
- **Eventos que publica**: Nenhum diretamente.
- **Eventos que consome**: Nenhum.
- **Invariantes**: Chassi único por tenant (Value Object, ver `shared/VALUE_OBJECTS.md`, a ser
  escrito).
- **Regras de negócio associadas**: D005/D006.
- **Estados**: Não aplicável.
- **Auditoria**: D007.
- **Linha do tempo**: parte do Veículo Tracionador.
- **Anexos suportados**: manual do fabricante (D024).
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: Nenhum.
- **Evoluções futuras previstas**: Nenhuma isolada.
- **Dependências obrigatórias**: Veículo Tracionador.
- **Dependências proibidas**: Financeiro, CT-e, Cliente.
- **Dono da Timeline**: Aggregate Veículo Tracionador.
- **Capacidade Offline**: Consulta Offline.

## Documento do Veículo

- **Objetivo**: Representa um documento obrigatório do veículo (CRLV, etc.) com validade —
  distinto de Licenciamento do Veículo, que é o processo anual específico.
- **Responsabilidades**: Guardar tipo, número e data de validade; gerar alerta de vencimento.
- **O que não faz**: Não é o mesmo que Licenciamento do Veículo.
- **Aggregate Root**: Não — parte do agregado Veículo Tracionador.
- **Bounded Context proprietário**: `fleet`
- **Principais relacionamentos**: Veículo Tracionador (N:1).
- **Eventos que publica**: `DocumentoDoVeiculoProximoDoVencimento` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: data de validade deve ser futura no momento do cadastro.
- **Regras de negócio associadas**: D005/D006, D007.
- **Estados**: `Válido` / `Vencido`.
- **Auditoria**: D007.
- **Linha do tempo**: parte do Veículo Tracionador.
- **Anexos suportados**: o próprio documento digitalizado (D024).
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: percentual de documentos em dia.
- **Documentos canônicos relacionados**: Nenhum.
- **Evoluções futuras previstas**: renovação automática via integração com órgãos de trânsito.
- **Dependências obrigatórias**: Veículo Tracionador.
- **Dependências proibidas**: Financeiro, CT-e, Cliente.
- **Dono da Timeline**: Aggregate Veículo Tracionador.
- **Capacidade Offline**: Consulta Offline.

## Apólice de Seguro Veicular

- **Objetivo**: Representa a cobertura de seguro vigente de um veículo.
- **Responsabilidades**: Ligar Veículo Tracionador a Seguradora; guardar vigência e cobertura.
- **O que não faz**: Não processa sinistro — isso é uma Ocorrência da Viagem (ver
  [`../flows/002-VIAGEM.md`](../flows/002-VIAGEM.md), Sinistro).
- **Aggregate Root**: Não — parte do agregado Veículo Tracionador.
- **Bounded Context proprietário**: `fleet`
- **Principais relacionamentos**: Veículo Tracionador (N:1); Seguradora (N:1, ver
  [`001-cadastros.md`](./001-cadastros.md)).
- **Eventos que publica**: `ApoliceProximaDoVencimento` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: vigência válida (fim posterior ao início).
- **Regras de negócio associadas**: D001, D005/D006.
- **Estados**: `Vigente` / `Vencida`.
- **Auditoria**: D007.
- **Linha do tempo**: parte do Veículo Tracionador.
- **Anexos suportados**: apólice digitalizada (D024).
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: custo de seguro por veículo.
- **Documentos canônicos relacionados**: Nenhum.
- **Evoluções futuras previstas**: acionamento eletrônico de sinistro.
- **Dependências obrigatórias**: Veículo Tracionador, Seguradora.
- **Dependências proibidas**: CT-e, Cliente, Financeiro (o custo é publicado via evento, nunca lido
  diretamente de `financial`).
- **Dono da Timeline**: Aggregate Veículo Tracionador.
- **Capacidade Offline**: Não.

## Leitura de Hodômetro

- **Objetivo**: Registro histórico (D037) de leituras de hodômetro do veículo, vindas de múltiplas
  origens (abastecimento, checklist, manual, despacho/encerramento de Viagem).
- **Responsabilidades**: Ser a fonte única da quilometragem do veículo — Hodômetro pertence a
  `fleet` (D034), mesmo quando o dado chega via evento de outro módulo.
- **O que não faz**: Não é editável — é inserida, nunca alterada (D037).
- **Aggregate Root**: Não — parte do agregado Veículo Tracionador; entidade **Histórica** (D037).
- **Bounded Context proprietário**: `fleet`
- **Principais relacionamentos**: Veículo Tracionador (N:1).
- **Eventos que publica**: `HodometroAtualizado` (novo).
- **Eventos que consome**: `AbastecimentoRegistrado` (`freight`), `ChecklistConcluido`
  (`maintenance`), `ViagemDespachada`/`ViagemFinalizada` (`freight` — **Reconciliado, V1
  Operational Hardening, Parte 2**) — lê a leitura informada nesses fluxos e gera um novo registro
  aqui, nunca o contrário.
- **Invariantes**: uma nova Leitura de Hodômetro nunca é menor que a última leitura registrada para
  o mesmo veículo — **"um abastecimento não pode reduzir o hodômetro"** (exemplo oficial registrado
  para `shared/INVARIANTS.md`).
- **Reconciliado (V1 Operational Hardening, Parte 2)**: duas novas origens, `DESPACHO_VIAGEM`/
  `ENCERRAMENTO_VIAGEM`, marcam precisamente as leituras de fronteira de uma Viagem (`KM_INICIAL`/
  `KM_FINAL`, já previsto abaixo em `VIAGEM_ID`) — mais confiável que tomar a primeira/última
  leitura cronológica com o mesmo `VIAGEM_ID`, que poderia ser corrompida por uma leitura de
  Checklist/Abastecimento não relacionada ao ciclo de despacho/encerramento. `TripOdometerRecorder`
  (`fleet`, não-HTTP, mesmo espírito de `VehicleAvailabilityProjector`) é o único ponto que grava
  essas duas origens, chamado por `DispatchTripHandler`/`FinishTripHandler` (`freight`) depois que
  a própria transação da Viagem já commitou — sem migration: `origem`/`viagem_id` já existiam como
  colunas livres (`String`/UUID nullable, sem CHECK), só o vocabulário Python ganhou dois valores
  novos.
- **Regras de negócio associadas**: D017/D018/D037 (histórica, append-only), D034 (dono único).
- **Estados**: Não aplicável — é ela própria um registro histórico.
- **Auditoria**: D007.
- **Linha do tempo**: parte do Veículo Tracionador.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: quilometragem rodada por período.
- **Documentos canônicos relacionados**: Nenhum.
- **Evoluções futuras previstas**: leitura automática via telemetria, eliminando digitação manual.
- **Dependências obrigatórias**: Veículo Tracionador.
- **Dependências proibidas**: Financeiro, CT-e, Cliente.
- **Dono da Timeline**: Aggregate Veículo Tracionador.
- **Capacidade Offline**: Sim (D039) — o app do motorista registra localmente e sincroniza depois.

## Licenciamento do Veículo

- **Objetivo**: Representa o processo/registro anual de licenciamento do veículo junto ao órgão de
  trânsito.
- **Responsabilidades**: Guardar exercício (ano), valor pago, data de quitação.
- **O que não faz**: Não é o mesmo que Documento do Veículo (genérico) — é o processo específico
  anual.
- **Aggregate Root**: Não — parte do agregado Veículo Tracionador.
- **Bounded Context proprietário**: `fleet`
- **Principais relacionamentos**: Veículo Tracionador (N:1).
- **Eventos que publica**: `LicenciamentoRegistrado`, `LicenciamentoProximoDoVencimento` (novos).
- **Eventos que consome**: Nenhum.
- **Invariantes**: um Licenciamento por veículo por exercício.
- **Regras de negócio associadas**: D001, D005/D006.
- **Estados**: `Pendente` / `Quitado` / `Vencido`.
- **Auditoria**: D007.
- **Linha do tempo**: parte do Veículo Tracionador.
- **Anexos suportados**: comprovante de pagamento (D024).
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: percentual de veículos licenciados em dia.
- **Documentos canônicos relacionados**: Nenhum.
- **Evoluções futuras previstas**: alerta automático de vencimento.
- **Dependências obrigatórias**: Veículo Tracionador.
- **Dependências proibidas**: CT-e, Cliente (referencia Conta a Pagar apenas via evento, nunca
  diretamente).
- **Dono da Timeline**: Aggregate Veículo Tracionador.
- **Capacidade Offline**: Consulta Offline.

## Categoria de Veículo

- **Objetivo**: Classifica o tipo de veículo/implemento (ex: truck, carreta, bitrem) para regras de
  negócio e relatórios.
- **Responsabilidades**: Ser referenciada por Veículo Tracionador e Implemento.
- **O que não faz**: Não define a Composição Veicular sozinha.
- **Aggregate Root**: Sim — entidade de **Referência** (D036), catálogo relativamente estático.
- **Bounded Context proprietário**: `fleet`
- **Principais relacionamentos**: Veículo Tracionador (N:1); Implemento (N:1).
- **Eventos que publica**: `CategoriaDeVeiculoCadastrada` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: nome único por tenant.
- **Regras de negócio associadas**: D001, D005/D006, D036.
- **Estados**: `Ativa` / `Inativa`.
- **Auditoria**: D007.
- **Linha do tempo**: cadastro, alterações.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: Nenhum.
- **Evoluções futuras previstas**: Nenhuma prevista.
- **Dependências obrigatórias**: Nenhuma.
- **Dependências proibidas**: Financeiro, CT-e, Cliente, Viagem.
- **Dono da Timeline**: Aggregate Categoria de Veículo (este próprio, embora simples).
- **Capacidade Offline**: Consulta Offline.

## Disponibilidade do Veículo

- **Objetivo**: Visão consolidada e derivada do status atual de um veículo (`Disponível`/`Em
  Viagem`/`Em Manutenção`/`Inativo`), para consulta rápida pelo Gestor Operacional.
- **Responsabilidades**: Agregar sinais de Viagem (alocação vigente), Ordem de Serviço (aberta) e o
  próprio cadastro do Veículo (Ativo/Inativo) em um único indicador de leitura.
- **O que não faz**: Não é a fonte de verdade de nenhum desses estados — é uma projeção (read
  model), mantida por `fleet` a partir de eventos de outros bounded contexts.
- **Aggregate Root**: Não — é um read model, não pertence a nenhum agregado transacional.
- **Bounded Context proprietário**: `fleet`
- **Principais relacionamentos**: Veículo Tracionador (1:1, projeção).
- **Eventos que publica**: Nenhum — é consumidora, não fonte de eventos de negócio.
- **Eventos que consome**: `ViagemDespachada`, `ViagemConcluida`, `ViagemInterrompida` (`freight`);
  `OrdemServicoAberta`, `OrdemServicoConcluida` (`maintenance`).
- **Invariantes**: reflete, com o menor atraso possível, a combinação dos eventos consumidos —
  nunca é editada diretamente por um usuário.
- **Regras de negócio associadas**: D032 — a entidade que originou cada evento não sabe que esta
  projeção o consome.
- **Estados**: `Disponível` / `Em Viagem` / `Em Manutenção` / `Inativo` (o próprio valor derivado).
- **Auditoria**: D007 — auditoria de quando cada recomputação ocorreu, não de "quem alterou"
  (ninguém altera diretamente).
- **Linha do tempo**: consumida pela timeline do Veículo Tracionador; não tem timeline própria.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: disponibilidade da frota (percentual de veículos `Disponível`).
- **Documentos canônicos relacionados**: Nenhum.
- **Evoluções futuras previstas**: prever indisponibilidade futura (ex: manutenção preventiva
  agendada) via IA.
- **Dependências obrigatórias**: Veículo Tracionador e, por evento, Viagem e Ordem de Serviço.
- **Dependências proibidas**: Financeiro, CT-e, Cliente — mesmo sendo derivada de eventos de
  `freight`/`maintenance`, nunca lê as tabelas desses módulos diretamente, só consome os eventos
  (D008).
- **Dono da Timeline**: Aggregate Veículo Tracionador.
- **Capacidade Offline**: Consulta Offline.
- **Reconciliado (Lote Frota e Manutenção, Parte 3)**: "Agregar sinais... em um único indicador"
  (Responsabilidades, acima) já previa múltiplas fontes concorrentes — implementado agora via
  `veiculo_impedimentos` (`../database/relational/004-frota.md`), um ledger interno de
  abertura/encerramento por Viagem/OS: o indicador só volta a `Disponível` quando nenhum
  impedimento seguir ativo, nunca ao encerrar apenas um deles.
