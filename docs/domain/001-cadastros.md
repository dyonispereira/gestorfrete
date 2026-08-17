# 001 — Cadastros

Entidades de cadastro-base do GestorFrete (Camada 0/1 de
[`../product/DEPENDENCY_MAP.md`](../product/DEPENDENCY_MAP.md)). Cada entidade segue o template
oficial definido em [`README.md`](./README.md) — este arquivo foi escrito com as 18 primeiras
seções do template, antes dos 4 campos adicionados a partir de `003-frota.md` (ver nota de
inconsistência pendente em `README.md`). Ver [`ENTITY_CATALOG.md`](./ENTITY_CATALOG.md) para o
índice completo desta categoria.

---

## Cliente

- **Objetivo**: Representa o cliente (embarcador) que contrata fretes da transportadora.
- **Responsabilidades**: Manter dados cadastrais e fiscais; ser referenciado por Cotação, Contrato
  de Frete e Viagem; agrupar Contato do Cliente.
- **O que não faz**: Não armazena histórico de fretes (pertence a `freight`, que apenas referencia
  o Cliente por ID); não define preço (isso é `pricing`); não representa o motorista autônomo.
- **Aggregate Root**: Sim — raiz do próprio agregado; Contato do Cliente é filho.
- **Bounded Context proprietário**: `crm`
- **Principais relacionamentos**: Contato do Cliente (1:N); Endereço (1:N, D182 — matriz, cobrança,
  entrega; substituiu o antigo VO único embutido, ver nota em `Endereço` abaixo); Cotação, Contrato
  de Frete, Viagem (referenciados por ID a partir de `freight`).
- **Eventos que publica**: `ClienteCadastrado`, `ClienteAtualizado`, `ClienteInativado` (novos —
  formalizados em `DOMAIN_EVENTS.md`).
- **Eventos que consome**: Nenhum.
- **Invariantes**: CNPJ/CPF único por tenant (D033/D005); Cliente `Inativo` não pode ser
  referenciado em nova Cotação (D016-like regra normativa).
- **Regras de negócio associadas**: D001 (soft delete), D005/D006 (tenant obrigatório).
- **Estados**: `Ativo` / `Inativo` — binário via soft delete (D001), sem máquina de estados rica.
- **Auditoria**: D007 — quem criou/alterou, quando.
- **Linha do tempo (Timeline Universal)**: Cadastro, alterações cadastrais, Cotações e Viagens
  vinculadas (por referência, D022).
- **Anexos suportados**: Contrato comercial assinado, documentos fiscais do cliente (D024).
- **Comentários suportados**: Sim — Comercial registra contexto de relacionamento (D023, interno).
- **KPIs relacionados**: Ticket médio por cliente, tamanho da carteira ativa.
- **Documentos canônicos relacionados**: Nenhum fluxo de negócio dedicado ainda — referenciado por
  [`../flows/002-VIAGEM.md`](../flows/002-VIAGEM.md) e [`../flows/005-FINANCEIRO.md`](../flows/005-FINANCEIRO.md).
- **Evoluções futuras previstas**: Portal do Cliente (autoatendimento — ver
  [`../product/VISION.md`](../product/VISION.md), capítulo 26); categoria/segmentação de cliente.

## Contato do Cliente

- **Objetivo**: Pessoa física de contato dentro do Cliente (quem recebe notificações, quem aprova
  cotações).
- **Responsabilidades**: Nome, cargo, telefone, e-mail; canal de notificação preferencial.
- **O que não faz**: Não substitui o Cliente como parte no Contrato de Frete.
- **Aggregate Root**: Não — parte do agregado Cliente.
- **Bounded Context proprietário**: `crm`
- **Principais relacionamentos**: Cliente (N:1).
- **Eventos que publica**: Nenhum diretamente (mudanças refletidas via `ClienteAtualizado`).
- **Eventos que consome**: Nenhum.
- **Invariantes**: Todo Contato pertence a exatamente um Cliente; e-mail, quando informado, é um
  E-mail válido (ver `VALUE_OBJECTS.md`, a ser escrito).
- **Regras de negócio associadas**: D005/D006.
- **Estados**: `Ativo` / `Inativo`.
- **Auditoria**: D007.
- **Linha do tempo**: Parte da timeline do Cliente — não tem timeline própria.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável (comentários ficam no Cliente).
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: Nenhum.
- **Evoluções futuras previstas**: Preferência de canal por contato (D023, ligado a
  `notification_center`).

## Fornecedor

- **Objetivo**: Representa um fornecedor de peças, serviços de recapagem ou outros insumos da
  operação.
- **Responsabilidades**: Dados cadastrais e fiscais; ser referenciado por Solicitação de Peça,
  Ordem de Serviço e Conta a Pagar.
- **O que não faz**: Não é o mesmo que Seguradora (entidade própria); não processa pagamento (isso
  é `financial`).
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `maintenance`
- **Principais relacionamentos**: Endereço (1:N, D182); Solicitação de Peça, Ordem de Serviço;
  Conta a Pagar (referenciado por ID a partir de `financial`).
- **Eventos que publica**: `FornecedorCadastrado`, `FornecedorInativado` (novos).
- **Eventos que consome**: Nenhum.
- **Invariantes**: CNPJ único por tenant; Fornecedor `Inativo` não pode ser vinculado a nova
  Solicitação de Peça.
- **Regras de negócio associadas**: D001, D005/D006.
- **Estados**: `Ativo` / `Inativo`.
- **Auditoria**: D007.
- **Linha do tempo**: Cadastro, alterações, OSs/compras vinculadas (por referência).
- **Anexos suportados**: Contrato de fornecimento, certidões (D024).
- **Comentários suportados**: Sim — Almoxarife/Analista de Frota registrando avaliação (D023).
- **KPIs relacionados**: Prazo médio de entrega, custo médio por fornecedor.
- **Documentos canônicos relacionados**: [`../flows/003-MANUTENCAO.md`](../flows/003-MANUTENCAO.md) (D035).
- **Evoluções futuras previstas**: Integração eletrônica de cotação/pedido (ver
  `003-MANUTENCAO.md`, Requisitos futuros).

## Motorista

- **Objetivo**: Representa o motorista, empregado ou autônomo, que executa viagens.
- **Responsabilidades**: Dados cadastrais, CNH/habilitações; vínculo a Usuário (acesso ao app); ser
  alocado a Viagens.
- **O que não faz**: Não controla a máquina de estados da Viagem (apenas participa dela); não é o
  mesmo que Funcionário (regras próprias de habilitação/CIOT que Funcionário não tem).
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `drivers`
- **Principais relacionamentos**: Usuário (1:1, acesso ao app); Documento do Motorista (1:N, D183 —
  CNH e demais documentos, nunca mais campos fixos nesta entidade); Viagem, CIOT (referenciados por
  ID).
- **Eventos que publica**: `MotoristaCadastrado` (novo), `HabilitacaoProximaDoVencimento` (já
  catalogado em [`../product/EVENT_MAP.md`](../product/EVENT_MAP.md)), `MotoristaBloqueado` (novo).
- **Eventos que consome**: Nenhum diretamente — reage à regra interna de validade da CNH.
- **Invariantes**: CNH deve estar válida para o motorista ser alocado a uma Viagem; motorista
  `Bloqueado` não pode iniciar viagem (exemplo oficial registrado para `INVARIANTS.md`).
- **Regras de negócio associadas**: D001, D005/D006.
- **Estados**: `Apto` / `Bloqueado` — simples, distinto da máquina de estados da Viagem.
- **Auditoria**: D007.
- **Linha do tempo**: Cadastro, viagens realizadas, ocorrências, bloqueios/desbloqueios.
- **Anexos suportados**: CNH digitalizada, exames toxicológicos (D024).
- **Comentários suportados**: Sim — Gestor Operacional registra avaliação (D023).
- **KPIs relacionados**: Viagens concluídas no prazo, taxa de ocorrências, indicadores de Meu
  Desempenho (ver [`../flows/010-APP_MOTORISTA.md`](../flows/010-APP_MOTORISTA.md)).
- **Documentos canônicos relacionados**: `010-APP_MOTORISTA.md` (Meu Desempenho, D035).
- **Evoluções futuras previstas**: Avaliação/rating do motorista pelo cliente.

## Funcionário

- **Objetivo**: Representa um colaborador interno da transportadora que não é motorista (ex:
  mecânico, almoxarife, financeiro).
- **Responsabilidades**: Dados cadastrais e funcionais (cargo, admissão); vínculo opcional a um
  Usuário.
- **O que não faz**: Não substitui Usuário (acesso ao sistema) nem Motorista.
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `identity_access`
- **Principais relacionamentos**: Usuário (0..1:1).
- **Eventos que publica**: `FuncionarioCadastrado` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: Um Funcionário só pode estar vinculado a um Usuário por vez.
- **Regras de negócio associadas**: D001, D005/D006.
- **Estados**: `Ativo` / `Inativo`.
- **Auditoria**: D007.
- **Linha do tempo**: Cadastro, alterações.
- **Anexos suportados**: Documentos admissionais (D024).
- **Comentários suportados**: Sim, interno (D023).
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: Nenhum.
- **Evoluções futuras previstas**: Estrutura organizacional/hierarquia.

## Seguradora

- **Objetivo**: Representa a seguradora responsável por apólices de veículos (e, futuramente,
  carga).
- **Responsabilidades**: Dados cadastrais; vínculo a Apólice de Seguro Veicular.
- **O que não faz**: Não processa sinistro (tratado como Ocorrência/fluxo de exceção — ver
  [`../flows/002-VIAGEM.md`](../flows/002-VIAGEM.md), Sinistro).
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `fleet`
- **Principais relacionamentos**: Apólice de Seguro Veicular (1:N, ver `003-frota.md`).
- **Eventos que publica**: `SeguradoraCadastrada` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: CNPJ único por tenant.
- **Regras de negócio associadas**: D001, D005/D006.
- **Estados**: `Ativa` / `Inativa`.
- **Auditoria**: D007.
- **Linha do tempo**: Cadastro, apólices vinculadas.
- **Anexos suportados**: Contrato de seguro (D024).
- **Comentários suportados**: Sim (D023).
- **KPIs relacionados**: Custo de seguro por veículo.
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: Integração eletrônica para acionamento de sinistro.

## Filial

- **Objetivo**: Representa uma unidade organizacional/operacional da transportadora (matriz ou
  filial).
- **Responsabilidades**: Agrupar Centro de Custo, Usuários e Veículos por unidade física.
- **O que não faz**: Não é um Tenant (Filial existe dentro de um único Tenant); não define
  permissões (isso é Papel/Permissão).
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `tenancy`
- **Principais relacionamentos**: Endereço (1:N, D182); Centro de Custo, Veículo Tracionador,
  Usuário (todos referenciados por ID).
- **Eventos que publica**: `FilialCadastrada` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: Toda Filial pertence a exatamente um Tenant; ao menos uma Filial (matriz) deve
  existir por tenant.
- **Regras de negócio associadas**: D005/D006, D001.
- **Estados**: `Ativa` / `Inativa`.
- **Auditoria**: D007.
- **Linha do tempo**: Cadastro, alterações.
- **Anexos suportados**: Nenhum específico.
- **Comentários suportados**: Sim, não crítico (D023).
- **KPIs relacionados**: Comparativo de performance entre filiais.
- **Documentos canônicos relacionados**: Nenhum.
- **Evoluções futuras previstas**: Hierarquia entre filiais (regional > filial).

## Centro de Custo

- **Objetivo**: Classificação usada para alocar despesas e apurar rentabilidade por unidade (ver
  [`../product/GLOSSARY.md`](../product/GLOSSARY.md)).
- **Responsabilidades**: Agrupar Lançamento de Centro de Custo; ser referenciado por Viagem, OS,
  Abastecimento.
- **O que não faz**: Não calcula margem sozinho — isso é
  [`../flows/005-FINANCEIRO.md`](../flows/005-FINANCEIRO.md) (D035).
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `financial`
- **Principais relacionamentos**: Filial (N:1); Lançamento de Centro de Custo (1:N).
- **Eventos que publica**: `CentroDeCustoCadastrado` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: Código do Centro de Custo único por tenant.
- **Regras de negócio associadas**: D001, D005/D006.
- **Estados**: `Ativo` / `Inativo`.
- **Auditoria**: D007.
- **Linha do tempo**: Cadastro, lançamentos vinculados.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Sim, uso do Financeiro (D023).
- **KPIs relacionados**: Custo por centro de custo.
- **Documentos canônicos relacionados**: `005-FINANCEIRO.md` (D035).
- **Evoluções futuras previstas**: Rateio automático configurável (já antecipado em
  `005-FINANCEIRO.md`).

## Tabela de Preço

- **Objetivo**: Define os valores praticados por rota/tipo de carga.
- **Responsabilidades**: Agrupar Item de Tabela de Preço; ser referenciada por Cotação.
- **O que não faz**: Não calcula o valor final de uma viagem específica sozinha — a Cotação aplica
  a tabela às condições concretas.
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `pricing`
- **Principais relacionamentos**: Item de Tabela de Preço (1:N); Cliente (opcional, tabela
  específica por cliente).
- **Eventos que publica**: `TabelaDePrecoPublicada`, `TabelaDePrecoDesativada` (novos).
- **Eventos que consome**: Nenhum.
- **Invariantes**: Apenas uma Tabela de Preço `Vigente` por combinação cliente/rota em um dado
  momento.
- **Regras de negócio associadas**: D001, D005/D006.
- **Estados**: `Rascunho` / `Vigente` / `Expirada`.
- **Auditoria**: D007.
- **Linha do tempo**: Criação, vigência, expiração.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Sim, negociação registrada (D023).
- **KPIs relacionados**: Ticket médio por tabela.
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: Precificação dinâmica sugerida por IA (ver
  [`../product/VISION.md`](../product/VISION.md), capítulo sobre Inteligência Artificial).

## Item de Tabela de Preço

- **Objetivo**: Linha de uma Tabela de Preço (valor por rota/tipo de carga/faixa de peso).
- **Responsabilidades**: Guardar o valor unitário aplicável.
- **O que não faz**: Não existe fora de uma Tabela de Preço.
- **Aggregate Root**: Não — parte do agregado Tabela de Preço.
- **Bounded Context proprietário**: `pricing`
- **Principais relacionamentos**: Tabela de Preço (N:1).
- **Eventos que publica**: Nenhum diretamente (mudanças refletidas via evento da Tabela).
- **Eventos que consome**: Nenhum.
- **Invariantes**: Valor deve ser maior que zero.
- **Regras de negócio associadas**: D005/D006.
- **Estados**: Segue o estado da Tabela de Preço.
- **Auditoria**: D007.
- **Linha do tempo**: Parte da timeline da Tabela de Preço.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: Nenhum.
- **Evoluções futuras previstas**: Nenhuma isolada.

## Usuário

- **Objetivo**: Representa uma conta de acesso ao sistema.
- **Responsabilidades**: Autenticação (fundação registrada, sem implementação ainda — ver
  [`../architecture/security-rbac-lgpd.md`](../architecture/security-rbac-lgpd.md)); vínculo a
  Papel(is).
- **O que não faz**: Não define, sozinho, o que o usuário pode fazer — isso é Papel/Permissão.
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `identity_access`
- **Principais relacionamentos**: Papel (N:N); Motorista (0..1:1); Funcionário (0..1:1).
- **Eventos que publica**: `UsuarioCriado`, `UsuarioDesativado` (novos).
- **Eventos que consome**: Nenhum.
- **Invariantes**: E-mail único por tenant.
- **Regras de negócio associadas**: D001, D005/D006.
- **Estados**: `Ativo` / `Inativo` / `Bloqueado`.
- **Auditoria**: D007 — crítico, é auditoria de acesso.
- **Linha do tempo**: Login, alterações de papel, bloqueios.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: Usuários ativos por tenant.
- **Documentos canônicos relacionados**: [`../architecture/security-rbac-lgpd.md`](../architecture/security-rbac-lgpd.md).
- **Evoluções futuras previstas**: Autenticação multifator.

## Papel

- **Objetivo**: Agrupa um conjunto de Permissões (RBAC) — corresponde, em nível de configuração, às
  15 personas de [`../product/PERSONAS.md`](../product/PERSONAS.md).
- **Responsabilidades**: Nomear e agrupar Permissões; ser atribuído a Usuários.
- **O que não faz**: Não concede acesso a um módulo específico sozinho — isso é a Permissão.
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `identity_access`
- **Principais relacionamentos**: Permissão (N:N); Usuário (N:N).
- **Eventos que publica**: `PapelCriado`, `PapelAtualizado` (novos).
- **Eventos que consome**: Nenhum.
- **Invariantes**: Nome do Papel único por tenant.
- **Regras de negócio associadas**: D005/D006.
- **Estados**: `Ativo` / `Inativo`.
- **Auditoria**: D007.
- **Linha do tempo**: Criação, alterações de permissões associadas.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: `RBAC_MATRIX.md` (a ser escrito, D035).
- **Evoluções futuras previstas**: Papéis customizáveis por tenant além dos padrão.

## Permissão

- **Objetivo**: Unidade atômica de autorização (ex: "criar Viagem", "aprovar OS acima da alçada").
- **Responsabilidades**: Ser referenciada por um ou mais Papéis.
- **O que não faz**: Não é atribuída diretamente a um Usuário — sempre via Papel.
- **Aggregate Root**: Não — catálogo de sistema, gerenciado internamente por `identity_access`.
- **Bounded Context proprietário**: `identity_access`
- **Principais relacionamentos**: Papel (N:N).
- **Eventos que publica**: Nenhum — catálogo estático por versão do sistema.
- **Eventos que consome**: Nenhum.
- **Invariantes**: Toda Permissão corresponde a uma ação real de um módulo existente.
- **Regras de negócio associadas**: D005/D006 aplica-se de forma diferente aqui — Permissões podem
  ser globais ao sistema, não necessariamente por tenant.
- **Estados**: Não aplicável.
- **Auditoria**: D007 — auditoria de uso, não de alteração (catálogo é do sistema, não do tenant).
- **Linha do tempo**: Não aplicável.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: Nenhum.
- **Documentos canônicos relacionados**: `RBAC_MATRIX.md` (a ser escrito, D035).
- **Evoluções futuras previstas**: Permissões granulares por campo, não apenas por ação/módulo.

## Rota Padrão

- **Objetivo**: Define uma rota reutilizável entre origem e destino frequentes.
- **Responsabilidades**: Agrupar Trecho de Rota; ser referenciada por Viagem/Cotação para acelerar
  o preenchimento.
- **O que não faz**: Não substitui a roteirização real (Mapbox) de uma viagem específica.
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `routing`
- **Principais relacionamentos**: Trecho de Rota (1:N); Praça de Pedágio (via Trecho).
- **Eventos que publica**: `RotaPadraoCadastrada` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: Deve ter ao menos um Trecho de Rota.
- **Regras de negócio associadas**: D001, D005/D006.
- **Estados**: `Ativa` / `Inativa`.
- **Auditoria**: D007.
- **Linha do tempo**: Criação, uso em viagens (por referência).
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Sim (D023).
- **KPIs relacionados**: Frequência de uso por rota.
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: Sugestão automática de rota por IA.

## Trecho de Rota

- **Objetivo**: Segmento de uma Rota Padrão entre dois pontos.
- **Responsabilidades**: Guardar distância, tempo estimado e Praças de Pedágio do trecho.
- **O que não faz**: Não existe fora de uma Rota Padrão.
- **Aggregate Root**: Não — parte do agregado Rota Padrão.
- **Bounded Context proprietário**: `routing`
- **Principais relacionamentos**: Rota Padrão (N:1); Praça de Pedágio (N:N).
- **Eventos que publica**: Nenhum.
- **Eventos que consome**: Nenhum.
- **Invariantes**: Distância deve ser maior que zero.
- **Regras de negócio associadas**: D005/D006.
- **Estados**: Segue a Rota Padrão.
- **Auditoria**: D007.
- **Linha do tempo**: Parte da timeline da Rota Padrão.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: Nenhum.
- **Evoluções futuras previstas**: Nenhuma isolada.

## Praça de Pedágio

- **Objetivo**: Representa um ponto de cobrança de pedágio, usado no cálculo do Custo Previsto de
  uma rota (ver [`../flows/005-FINANCEIRO.md`](../flows/005-FINANCEIRO.md)).
- **Responsabilidades**: Guardar localização e valor de referência.
- **O que não faz**: Não registra o pedágio efetivamente pago em uma viagem — isso é uma despesa em
  Custo Realizado (`005-FINANCEIRO.md`).
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `routing`
- **Principais relacionamentos**: Trecho de Rota (N:N).
- **Eventos que publica**: `PracaDePedagioCadastrada` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: Valor de referência deve ser maior ou igual a zero.
- **Regras de negócio associadas**: D001, D005/D006.
- **Estados**: `Ativa` / `Inativa`.
- **Auditoria**: D007.
- **Linha do tempo**: Cadastro, alterações de valor.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: Custo de pedágio previsto vs. realizado (ver `005-FINANCEIRO.md`).
- **Documentos canônicos relacionados**: Nenhum.
- **Evoluções futuras previstas**: Integração com tag de pedágio automática.

---

> **Duas entidades novas abaixo (D182/D183), identificadas ao modelar a camada relacional
> (`docs/database/relational/002-cadastros.md`) — template completo de 22 campos, mesmo quando as
> 16 entidades originais deste arquivo ainda usam o template de 18 (nota de inconsistência pendente
> em `README.md`); entidade nova sempre usa o template vigente no momento em que nasce.**

## Endereço

- **Objetivo**: Representa um endereço físico associado a Cliente, Fornecedor ou Filial — matriz,
  cobrança, entrega, ou outro papel, com suporte nativo a múltiplos endereços por entidade (D182).
- **Responsabilidades**: Guardar os componentes do endereço (logradouro, número, complemento,
  bairro, cidade, UF, CEP) e o papel (`TIPO_ENDERECO`) que este endereço cumpre para a
  entidade-dona.
- **O que não faz**: Não existe sozinho — sempre pertence a exatamente uma entidade-dona.
- **Aggregate Root**: Não — parte do agregado da entidade-dona (Cliente, Fornecedor ou Filial,
  conforme `ENTIDADE_TIPO`).
- **Bounded Context proprietário**: Segue a entidade-dona (`crm` para Cliente, `maintenance` para
  Fornecedor, `tenancy` para Filial) — Endereço em si não introduz um bounded context novo.
- **Principais relacionamentos**: Entidade-dona (referência polimórfica — Cliente/Fornecedor/
  Filial).
- **Eventos que publica**: Nenhum diretamente (mudanças refletidas via evento da entidade-dona).
- **Eventos que consome**: Nenhum.
- **Invariantes**: Sempre referencia exatamente uma entidade-dona; no máximo um endereço `Principal`
  vigente por entidade-dona (quando `TIPO_ENDERECO = Principal`).
- **Regras de negócio associadas**: D005/D006, D182 (entidade própria sempre que a cardinalidade
  puder ser maior que um).
- **Estados**: Não aplicável.
- **Auditoria**: D007.
- **Linha do tempo**: Parte da timeline da entidade-dona.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: Nenhum.
- **Evoluções futuras previstas**: Validação de CEP via integração com API de correios.
- **Dependências obrigatórias**: Cliente, Fornecedor ou Filial (exatamente um).
- **Dependências proibidas**: Viagem, CT-e, Financeiro, Pneu.
- **Dono da Timeline**: A entidade-dona (via referência).
- **Capacidade Offline**: Consulta Offline.

## Documento do Motorista

- **Objetivo**: Representa um documento do Motorista com validade — CNH, RG, Exame Toxicológico,
  Registro ANTT (autônomo) — consolidados em um `TIPO_DOCUMENTO` fechado e extensível (D183), nunca
  campos fixos na própria tabela de Motorista.
- **Responsabilidades**: Guardar número, categoria (quando aplicável, ex: CNH), validade e a
  digitalização do documento; disparar alerta de vencimento.
- **O que não faz**: Não decide sozinho o `STATUS_APTIDAO` do Motorista — apenas fornece o dado
  (validade da CNH) que a regra de negócio já existente em Motorista consulta.
- **Aggregate Root**: Não — parte do agregado Motorista.
- **Bounded Context proprietário**: `drivers`
- **Principais relacionamentos**: Motorista (N:1).
- **Eventos que publica**: `DocumentoDoMotoristaProximoDoVencimento` (novo — mesmo padrão de
  `DocumentoDoVeiculoProximoDoVencimento`, `003-frota.md`).
- **Eventos que consome**: Nenhum.
- **Invariantes**: data de validade deve ser futura no momento do cadastro, quando aplicável (nem
  todo `TIPO_DOCUMENTO` tem validade, ex: RG); a CNH continua sendo o gatilho de
  `Motorista.STATUS_APTIDAO`, agora lida a partir daqui em vez de um campo fixo.
- **Regras de negócio associadas**: D005/D006, D007, D183.
- **Estados**: `Válido` / `Vencido`.
- **Auditoria**: D007.
- **Linha do tempo**: Parte da timeline do Motorista.
- **Anexos suportados**: o próprio documento digitalizado (D024).
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: percentual de motoristas com documentação em dia.
- **Documentos canônicos relacionados**: Nenhum.
- **Evoluções futuras previstas**: leitura automática via OCR (`Leitura por Visão Computacional`,
  [`012-ia.md`](./012-ia.md)) — a Leitura propõe o preenchimento, nunca aplica automaticamente
  (D161/D164).
- **Dependências obrigatórias**: Motorista.
- **Dependências proibidas**: Viagem, CT-e, Financeiro, Pneu.
- **Dono da Timeline**: Aggregate Motorista.
- **Capacidade Offline**: Consulta Offline.
