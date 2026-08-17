# PRODUCT_MAP.md — Mapa Completo do Produto

Este documento lista **todas** as áreas funcionais planejadas do GestorFrete, organizadas por
categoria de produto. É deliberadamente raso: apenas nomes organizados, sem descrição, sem
prioridade e sem detalhe de implementação — isso é o que os próximos documentos fazem
([`MODULE_PRIORITY.md`](./MODULE_PRIORITY.md) para versionamento,
[`DEPENDENCY_MAP.md`](./DEPENDENCY_MAP.md) para dependências,
[`BUSINESS_RULES.md`](./BUSINESS_RULES.md) e [`SCREENS.md`](./SCREENS.md), quando escritos, para
profundidade).

**Importante — isto não é a arquitetura de código.** As categorias abaixo são um mapa de produto
(o que o usuário reconhece como área do sistema), não os bounded contexts do backend (ver
[`../architecture/ddd.md`](../architecture/ddd.md)). Um bounded context pode alimentar várias
categorias aqui, e uma categoria aqui pode ser servida por mais de um bounded context. Este
documento **não cria, renomeia nem propõe** nenhum módulo técnico novo — isso continua sujeito à
regra de arquitetura congelada (ver [`DECISIONS.md`](./DECISIONS.md), D011).

---

## Cadastros

- Clientes (Embarcadores)
- Motoristas
- Veículos (Cavalo Mecânico)
- Carretas / Implementos
- Fornecedores
- Filiais
- Centros de Custo
- Tabelas de Preço
- Rotas Padrão
- Praças de Pedágio
- Seguradoras
- Usuários e Permissões

## Operação

- Viagens
- Coletas
- Entregas
- Ocorrências
- Roteirização
- Despacho
- Painel de Viagens Ativas
- Reatribuição de Viagem
- Comprovante de Entrega (Canhoto)
- Romaneio

## Documentos Fiscais

- Emissão de CT-e
- Emissão de MDF-e
- CIOT
- Cancelamento de Documento Fiscal
- Consulta de Status na SEFAZ
- Histórico de Documentos

## Financeiro

- Contas a Pagar
- Contas a Receber
- Fluxo de Caixa
- DRE
- Apuração por Centro de Custo
- Adiantamentos
- Haveres de Motorista
- Conciliação Bancária
- Repasse a Terceiros
- Faturamento de Fretes

## Frota e Manutenção

- Ficha do Veículo
- Ordens de Serviço
- Ciclo de Pneu
- Recapagem
- Checklist de Saída
- Checklist de Retorno
- Manutenção Preventiva
- Manutenção Corretiva
- Histórico de Manutenção
- Estoque de Peças (Almoxarifado)
- Licenciamento de Veículo
- Seguro de Veículo

## Motoristas

- Ficha do Motorista
- CNH e Habilitações
- Escala de Viagens
- Avaliação de Motorista
- Ocorrências do Motorista
- Treinamentos

## Comercial e CRM

- Funil de Oportunidades
- Propostas Comerciais
- Contratos de Frete
- Tabela de Preços Comercial
- Simulador de Frete
- Marketplace de Cargas
- Carteira de Clientes

## Billing e Assinatura (SaaS)

- Planos
- Assinatura do Tenant
- Cobrança Recorrente
- Histórico de Faturas
- Upgrade/Downgrade de Plano
- Onboarding de Conta

## Compliance e Auditoria

- Trilha de Auditoria
- Logs de Acesso
- Gestão de Permissões (RBAC)
- Consentimento LGPD
- Exportação de Dados do Titular

## Relatórios e BI

- Relatório de Fretes
- Relatório Financeiro
- Relatório de Manutenção
- Relatório de Motoristas
- Dashboard Executivo
- Exportação (PDF/Excel/CSV)
- Indicadores Operacionais

## Inteligência Artificial

- Sugestão de Manutenção Preventiva
- Precificação Dinâmica Sugerida
- Previsão de Prazo de Entrega
- Otimização de Rota
- Detecção de Anomalias Financeiras

## Comunicação e Notificações

- Central de Notificações
- Preferências de Canal
- Alertas Operacionais
- Alertas de Manutenção

## Suporte e Atendimento

- Central de Tickets
- Base de Conhecimento
- Chat de Suporte

## Portais Externos

- Portal do Cliente
- Portal do Motorista
- Aplicativo Mobile do Motorista
- Landing Page
- Cadastro Self-Service

## Integrações

- Integração SEFAZ
- Integração ANTT/CIOT
- Integração Mapbox
- Integração GestorPec
- Integração GestorContábil
- API Pública

## Rastreamento e Telemetria

- Posição em Tempo Real
- Histórico de Rota Percorrida
- Telemetria de Veículo
- Geofencing
- Alertas de Desvio de Rota

## Workflow e Automação

- Fluxos de Aprovação
- Automações Configuráveis

## Configurações da Conta

- Dados da Empresa
- Identidade Visual (White-label)
- Timezone e Localidade
- Preferências Gerais

## Armazenamento e Arquivos

- Repositório de Anexos

## Administração da Plataforma

- Gestão de Tenants
- Monitoramento da Plataforma
- Gestão de Planos Globais
- Auditoria Cross-tenant

---

## Contagem

20 categorias, 120 áreas funcionais listadas nesta versão do mapa. Este número cresce conforme o
produto evolui — este documento é atualizado por sprint, junto com os demais documentos de
`docs/product/`, nunca de uma vez só.
