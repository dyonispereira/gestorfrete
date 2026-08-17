# PERSONAS.md — GestorFrete ERP Enterprise

Este documento detalha as 15 personas do GestorFrete. As primeiras 11 atuam **dentro de uma
transportadora tenant** (funcionários da transportadora ou seu cliente externo). As últimas 4 —
Consultor Comercial, Implantação, Suporte e Administrador SaaS — são papéis da **equipe do próprio
GestorFrete**, com necessidades e permissões de natureza diferente (acesso cross-tenant controlado,
não acesso a um único tenant). Essa distinção é proposital e deve ser respeitada em qualquer decisão
futura de permissão/RBAC
(ver [`../architecture/security-rbac-lgpd.md`](../architecture/security-rbac-lgpd.md)).

Cada persona segue a mesma estrutura: objetivos, responsabilidades, dores, indicadores,
permissões, telas utilizadas, frequência de uso e principais fluxos.

---

## 1. Diretor da Transportadora

- **Objetivos**: ter visão consolidada do negócio para tomar decisões estratégicas; garantir a
  rentabilidade da operação.
- **Responsabilidades**: definir metas, aprovar investimentos relevantes (compra de veículos,
  expansão), acompanhar indicadores gerais da empresa.
- **Dores**: falta de visibilidade em tempo real; decisões baseadas em dados atrasados ou
  planilhas paralelas; dificuldade de comparar performance entre filiais/centros de custo.
- **Indicadores**: margem por frete, custo por km rodado, faturamento mensal, inadimplência de
  clientes, retorno sobre investimento da frota.
- **Permissões**: acesso total ao tenant — leitura e escrita em todos os módulos, incluindo
  configurações de conta e gestão de usuários.
- **Telas utilizadas**: dashboard executivo (`analytics`), `financial`, `reporting`, `settings`,
  visão geral de `fleet`.
- **Frequência de uso**: diária, em sessões curtas (dashboard); semanal/mensal em sessões mais
  profundas (revisão financeira).
- **Principais fluxos**: revisar o dashboard executivo pela manhã; aprovar despesas relevantes;
  revisar relatório financeiro mensal; conceder/revisar permissões de outros usuários.

## 2. Gestor Operacional

- **Objetivos**: garantir que os fretes sejam despachados e concluídos no prazo, com uso eficiente
  da frota.
- **Responsabilidades**: alocar motorista e veículo a cada frete; monitorar viagens em andamento;
  resolver imprevistos operacionais (quebra, atraso, reatribuição).
- **Dores**: falta de visibilidade em tempo real de onde está cada veículo/motorista; retrabalho
  para reatribuir um frete quando algo dá errado no meio da operação.
- **Indicadores**: percentual de fretes concluídos no prazo, taxa de ocupação da frota, tempo médio
  entre criação e despacho de um frete.
- **Permissões**: leitura e escrita em `freight`, `fleet`, `drivers`, `routing` e `tracking`;
  leitura (sem edição de valores) em `financial`.
- **Telas utilizadas**: painel de despacho (`freight`), mapa de rastreamento (`tracking`/
  `routing`), disponibilidade de frota (`fleet`).
- **Frequência de uso**: contínua ao longo de todo o expediente — é a persona de uso mais intenso
  do Portal do Gestor.
- **Principais fluxos**: criar e despachar um frete; reatribuir motorista/veículo diante de um
  imprevisto; acompanhar uma viagem em tempo real; confirmar conclusão de uma entrega.

## 3. Analista de Frota

- **Objetivos**: manter a frota disponível, segura e com custo de manutenção sob controle.
- **Responsabilidades**: monitorar ciclo de pneu de cada veículo; agendar manutenções preventivas;
  controlar documentação e licenciamento da frota.
- **Dores**: manutenção reativa por falta de histórico centralizado por veículo; dificuldade de
  prever quando um veículo vai precisar de manutenção antes que a quebra aconteça.
- **Indicadores**: custo de manutenção por veículo/km rodado, percentual de manutenções preventivas
  vs. corretivas, disponibilidade da frota (veículos aptos vs. total).
- **Permissões**: leitura e escrita em `fleet` e `maintenance`; leitura em `drivers` (associação
  veículo-motorista).
- **Telas utilizadas**: ficha do veículo (`fleet`), ciclo de pneu e ordens de serviço
  (`maintenance`).
- **Frequência de uso**: diária.
- **Principais fluxos**: abrir uma ordem de serviço; registrar troca ou recapagem de pneu; agendar
  manutenção preventiva; bloquear um veículo como indisponível.

## 4. Mecânico

- **Objetivos**: executar manutenções corretamente, com registro completo do que foi feito no
  veículo.
- **Responsabilidades**: executar ordens de serviço atribuídas; registrar peças utilizadas;
  atualizar o status do veículo após o reparo.
- **Dores**: falta de histórico do veículo disponível na hora do reparo; retrabalho por não saber
  o que já foi trocado anteriormente.
- **Indicadores**: tempo médio de execução de uma ordem de serviço; taxa de reincidência do mesmo
  problema no mesmo veículo.
- **Permissões**: leitura e escrita restritas às suas ordens de serviço em `maintenance`; leitura da
  ficha técnica do veículo em `fleet`.
- **Telas utilizadas**: lista de ordens de serviço atribuídas, ficha técnica do veículo, histórico
  de manutenção.
- **Frequência de uso**: diária, durante o turno de trabalho na oficina.
- **Principais fluxos**: receber uma ordem de serviço; consultar o histórico do veículo; registrar
  peças e serviço executado; encerrar a ordem de serviço.

## 5. Almoxarife

- **Objetivos**: garantir que peças e insumos estejam disponíveis quando a oficina precisar, sem
  manter estoque parado em excesso.
- **Responsabilidades**: controlar entrada e saída de peças; vincular peças usadas a ordens de
  serviço; gerenciar fornecedores de insumos.
- **Dores**: falta de rastreabilidade de qual ordem de serviço consumiu qual peça; ruptura de
  estoque de itens críticos sem aviso prévio.
- **Indicadores**: giro de estoque, itens em ruptura, custo de peças por veículo.
- **Permissões**: leitura e escrita no controle de estoque (`maintenance`/`storage`); leitura das
  ordens de serviço em `maintenance`.
- **Telas utilizadas**: controle de estoque de peças, vínculo peça–ordem de serviço.
- **Frequência de uso**: diária.
- **Principais fluxos**: registrar entrada de peça (compra); baixar peça em uma ordem de serviço;
  conferir estoque mínimo; solicitar reposição.

## 6. Financeiro

- **Objetivos**: manter o caixa da transportadora saudável e previsível.
- **Responsabilidades**: conciliar contas a pagar/receber; gerenciar adiantamentos e haveres de
  motoristas; controlar centros de custo.
- **Dores**: reconciliação manual concentrada no fim do mês; dificuldade de rastrear adiantamentos
  ainda não baixados.
- **Indicadores**: fluxo de caixa, inadimplência de clientes, custo por centro de custo, saldo de
  adiantamentos em aberto.
- **Permissões**: leitura e escrita total em `financial`; leitura em `freight` (valores de frete) e
  `drivers` (para haveres/adiantamentos).
- **Telas utilizadas**: contas a pagar/receber, adiantamentos, centros de custo, relatórios
  financeiros (`reporting`).
- **Frequência de uso**: diária.
- **Principais fluxos**: registrar um adiantamento; conciliar o haver de um motorista; lançar uma
  despesa em um centro de custo; fechar o caixa do período.

## 7. Faturista

- **Objetivos**: emitir e conferir corretamente os documentos fiscais de cada frete, garantindo
  faturamento sem erro.
- **Responsabilidades**: emitir CT-e/MDF-e; conferir romaneio e canhoto antes de faturar; corrigir
  divergências fiscais.
- **Dores**: divergência entre o que foi efetivamente transportado e o documento fiscal emitido;
  canhoto que demora a retornar, atrasando o faturamento.
- **Indicadores**: tempo entre a entrega e o faturamento, percentual de documentos rejeitados pela
  SEFAZ, quantidade de canhotos pendentes.
- **Permissões**: leitura e escrita em `documents`; leitura em `freight` (dados do frete a
  faturar).
- **Telas utilizadas**: emissão de CT-e/MDF-e, conferência de canhoto, fila de faturamento.
- **Frequência de uso**: diária.
- **Principais fluxos**: emitir CT-e ao despachar um frete; emitir MDF-e ao consolidar cargas;
  registrar o retorno do canhoto; disparar o faturamento.

## 8. Comercial

- **Objetivos**: captar e manter clientes (embarcadores), garantindo volume de frete rentável.
- **Responsabilidades**: negociar tabelas de preço; prospectar novos clientes; acompanhar o
  relacionamento comercial com a carteira existente.
- **Dores**: falta de visibilidade sobre a capacidade real da frota na hora de fechar um frete;
  retrabalho ao negociar preço sem referência histórica confiável.
- **Indicadores**: novos clientes captados por período, ticket médio por frete, taxa de conversão
  de proposta.
- **Permissões**: leitura e escrita em `crm` e `pricing`; leitura em `fleet` (capacidade
  disponível) e `freight` (histórico de fretes por cliente).
- **Telas utilizadas**: funil de oportunidades (`crm`), tabela de preços (`pricing`), histórico de
  fretes por cliente.
- **Frequência de uso**: diária.
- **Principais fluxos**: cadastrar um lead/oportunidade; montar uma proposta de preço; converter
  oportunidade em contrato ativo; acompanhar a carteira de clientes.

## 9. Motorista

- **Objetivos**: executar a viagem com o mínimo de fricção burocrática; saber com clareza quanto
  vai receber.
- **Responsabilidades**: realizar coleta e entrega; registrar o canhoto; reportar problemas no
  veículo; prestar contas de adiantamentos recebidos.
- **Dores**: pouca visibilidade sobre adiantamentos e haveres; burocracia demorada para reportar um
  problema ou registrar uma entrega, especialmente com conectividade ruim na estrada.
- **Indicadores** (vistos pelo próprio motorista): viagens concluídas no prazo, saldo de
  adiantamento, histórico de haveres.
- **Permissões**: acesso restrito e estritamente próprio — apenas suas viagens, seus documentos e
  seus adiantamentos/haveres; sem acesso a dados de outros motoristas ou à operação como um todo.
- **Telas utilizadas**: aplicativo mobile (`mobile`) — viagem atual, registro de canhoto,
  adiantamentos/haveres, reporte de problema no veículo.
- **Frequência de uso**: contínua durante a viagem, múltiplas interações ao longo do dia.
- **Principais fluxos**: aceitar/iniciar uma viagem; registrar a coleta; registrar a entrega e o
  canhoto; solicitar ou consultar um adiantamento; reportar um problema mecânico.

## 10. Cliente (Embarcador)

- **Objetivos**: saber onde está sua carga; ter acesso fácil aos documentos fiscais do frete
  contratado.
- **Responsabilidades** (dentro do produto): acompanhar o status do frete; validar e baixar
  documentos.
- **Dores**: falta de visibilidade do status da carga sem precisar ligar para a transportadora.
- **Indicadores**: não há indicador operacional próprio — sua "métrica" é a satisfação com o
  serviço (NPS), medida pela transportadora.
- **Permissões**: acesso somente aos próprios fretes e documentos, via Portal do Cliente, sem
  nenhum acesso a dados internos da transportadora.
- **Telas utilizadas**: Portal do Cliente — status de coleta/entrega, documentos fiscais, canhoto.
- **Frequência de uso**: esporádica, concentrada em torno de cada frete ativo.
- **Principais fluxos**: consultar o status da carga; baixar CT-e/MDF-e; visualizar o canhoto de
  entrega.

## 11. Auditor

- **Objetivos**: verificar a conformidade e a correção das operações registradas no sistema, sem
  interferir na operação em si.
- **Responsabilidades**: revisar lançamentos financeiros, viagens realizadas, dados de motoristas,
  checklists de manutenção e a trilha de auditoria; identificar inconsistências ou não
  conformidades.
- **Dores**: hoje precisa solicitar exports/relatórios manualmente a terceiros para conseguir
  auditar, o que atrasa e limita a profundidade do trabalho.
- **Indicadores**: número de inconsistências encontradas, cobertura da auditoria (percentual de
  registros revisados no período), tempo total de auditoria.
- **Permissões**: **somente leitura, sem exceção**, sobre `financial`, `freight` (viagens),
  `drivers`, a trilha de auditoria (`audit`) e `maintenance` (incluindo checklists) — nenhuma tela
  permite criar, editar ou excluir para este perfil, em nenhuma hipótese. Esta é uma restrição de
  RBAC a ser tratada como inegociável (ver
  [`../architecture/security-rbac-lgpd.md`](../architecture/security-rbac-lgpd.md)).
- **Telas utilizadas**: visão financeira somente leitura, histórico de viagens, ficha de
  motoristas, trilha de auditoria (`audit`), checklists e ordens de serviço (`maintenance`) — todas
  em modo de consulta.
- **Frequência de uso**: recorrente, em ciclos periódicos de auditoria (ex: mensal/trimestral),
  além de consultas pontuais motivadas por alguma investigação específica — persona de uso muito
  frequente apesar do escopo restrito.
- **Principais fluxos**: revisar lançamentos financeiros de um período; conferir viagens concluídas
  contra os documentos fiscais correspondentes; verificar checklists de manutenção preenchidos;
  consultar a trilha de auditoria de um registro específico; exportar evidências para um relatório
  de auditoria externo.

---

## 12. Consultor Comercial *(equipe GestorFrete)*

- **Objetivos**: converter prospects em clientes através de demonstrações eficazes; viabilizar a
  fase inicial de implantação até a entrega formal para a equipe de Implantação.
- **Responsabilidades**: realizar demonstrações do produto; conduzir implantações iniciais;
  elaborar propostas comerciais; realizar visitas a prospects e clientes.
- **Dores**: ambientes de demonstração desatualizados ou não representativos da operação real do
  prospect; falta de um ambiente sandbox consistente para demonstrar sem arriscar dados reais.
- **Indicadores**: número de demonstrações realizadas, taxa de conversão de demonstração em
  contrato fechado, tempo entre a primeira visita e a assinatura.
- **Permissões**: acesso amplo, porém **temporário e escopado** — concedido para um ambiente de
  demonstração/sandbox ou para o tenant de um prospect durante o período de venda/implantação
  inicial, com expiração automática ao fim do período combinado. Nunca acesso permanente a um
  tenant já implantado e entregue à operação.
- **Telas utilizadas**: ambiente de demonstração (`onboarding`, dados de exemplo), ferramentas de
  proposta (`pricing`, `crm`).
- **Frequência de uso**: variável, concentrada em ciclos de venda — picos de uso intensos por
  prospect, seguidos de inatividade até o próximo.
- **Principais fluxos**: agendar e conduzir uma demonstração; gerar uma proposta comercial;
  configurar um ambiente de teste para um prospect; realizar a implantação inicial e transferir a
  conta para Implantação/Suporte.

## 13. Implantação *(equipe GestorFrete)*

- **Objetivos**: colocar uma nova transportadora operando no sistema o mais rápido possível, com
  dados corretos desde o início.
- **Responsabilidades**: conduzir o onboarding de contas (especialmente Enterprise), migrar dados
  iniciais, configurar o tenant.
- **Dores**: dados de origem desorganizados (planilhas inconsistentes do cliente); prazo apertado
  de virada de sistema.
- **Indicadores**: tempo de implantação, percentual de contas que ativam com sucesso dentro do
  prazo combinado.
- **Permissões**: acesso operacional amplo dentro do tenant em implantação, com trilha de
  auditoria; sem acesso cross-tenant além do necessário para o trabalho em curso.
- **Telas utilizadas**: ferramentas de onboarding e configuração de tenant (`onboarding`,
  `settings`), importação de dados.
- **Frequência de uso**: intensiva durante o período de implantação de cada cliente; esporádica
  depois disso.
- **Principais fluxos**: configurar um tenant novo; importar cadastros iniciais (frota,
  motoristas, clientes); validar dados junto ao cliente; transferir a conta para o Suporte.

## 14. Suporte *(equipe GestorFrete)*

- **Objetivos**: resolver dúvidas e problemas dos usuários das transportadoras com rapidez.
- **Responsabilidades**: atender tickets; reproduzir e escalar bugs; orientar o uso correto do
  produto.
- **Dores**: falta de contexto suficiente sobre o tenant do cliente para diagnosticar o problema
  rapidamente.
- **Indicadores**: tempo de primeira resposta, tempo de resolução, satisfação pós-atendimento.
- **Permissões**: leitura ampla (com trilha de auditoria) sobre tenants para diagnóstico; escrita
  limitada a ações de suporte assistido, nunca a alterações de negócio arbitrárias.
- **Telas utilizadas**: central de tickets (`support`), visão de tenant para diagnóstico.
- **Frequência de uso**: contínua durante o horário de atendimento.
- **Principais fluxos**: triagem de um ticket; reproduzir o problema no tenant do cliente;
  responder e orientar o cliente; escalar um bug para o time de produto/engenharia.

## 15. Administrador SaaS *(equipe GestorFrete)*

- **Objetivos**: manter a plataforma saudável, segura e operando corretamente para todos os
  tenants.
- **Responsabilidades**: gerenciar planos e assinaturas na plataforma; monitorar a saúde técnica
  multi-tenant; administrar configurações globais.
- **Dores**: identificar rapidamente se um problema é de um tenant específico ou da plataforma como
  um todo.
- **Indicadores**: disponibilidade da plataforma, número de tenants ativos, saúde de
  billing/assinaturas.
- **Permissões**: o único perfil com acesso administrativo cross-tenant — por isso mesmo o mais
  sensível, e o que deve ser mais fortemente controlado e auditado de todo o sistema.
- **Telas utilizadas**: painel administrativo da plataforma (billing/subscription cross-tenant,
  saúde técnica, `analytics` de plataforma).
- **Frequência de uso**: diária.
- **Principais fluxos**: monitorar a saúde geral da plataforma; gerenciar a assinatura/plano de um
  tenant específico; investigar um incidente cross-tenant; administrar configurações globais da
  plataforma.
