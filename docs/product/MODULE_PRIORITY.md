# MODULE_PRIORITY.md — Priorização por Versão

Este documento decide, para cada uma das 120 áreas funcionais de [`PRODUCT_MAP.md`](./PRODUCT_MAP.md),
em qual versão ela entra. O objetivo é impedir a tentação natural de um projeto ambicioso: tentar
desenvolver tudo ao mesmo tempo. Nada aqui é implementado ainda — este é o plano de ordem, não um
compromisso de prazo.

## Critério de priorização

Uma área entra em V1 apenas se for indispensável para o **menor loop operacional completo**: uma
transportadora consegue cadastrar cliente/motorista/veículo, criar e executar uma viagem, emitir o
documento fiscal correspondente, faturar e pagar o motorista — sem isso, não há produto usável, só
partes soltas. Tudo o que não é indispensável a esse loop é adiado, mesmo que seja simples de
construir. A ordem também respeita [`DEPENDENCY_MAP.md`](./DEPENDENCY_MAP.md): nenhuma área entra
em uma versão antes de todas as áreas de que ela depende.

As versões aqui **não são datas** — são fatias de escopo. O tempo de cada uma é uma decisão de
planejamento separada, a ser registrada em [`ROADMAP.md`](./ROADMAP.md) quando esse documento for
escrito. Alinhamento de referência com o horizonte de 5 anos: V1 ≈ Ano 1, V2 ≈ Ano 2, V3 ≈ Ano 3,
V4 ≈ Ano 4 de [`VISION.md`](./VISION.md) (capítulo 18).

---

## V1 — Loop operacional completo (62 áreas)

A transportadora consegue operar do zero ao fim: cadastrar, viajar, faturar, pagar. Sem
roteirização automática, sem app mobile, sem IA, sem CRM — só o essencial que já resolve o problema
central descrito em [`VISION.md`](./VISION.md), capítulo 7 ("Problemas que o GestorFrete resolve").

| Categoria | Itens |
|---|---|
| Cadastros | Clientes, Motoristas, Veículos, Carretas/Implementos, Fornecedores, Filiais, Centros de Custo, Tabelas de Preço, Usuários e Permissões |
| Operação | Viagens, Coletas, Entregas, Ocorrências, Comprovante de Entrega (Canhoto), Romaneio, Despacho, Painel de Viagens Ativas, Reatribuição de Viagem |
| Documentos Fiscais | Emissão de CT-e, Emissão de MDF-e, Cancelamento de Documento Fiscal, Consulta de Status na SEFAZ, Histórico de Documentos |
| Financeiro | Contas a Pagar, Contas a Receber, Faturamento de Fretes, Adiantamentos, Haveres de Motorista, Fluxo de Caixa |
| Frota e Manutenção | Ficha do Veículo, Ordens de Serviço, Manutenção Preventiva, Manutenção Corretiva, Histórico de Manutenção, Checklist de Saída, Checklist de Retorno |
| Motoristas | Ficha do Motorista, CNH e Habilitações, Escala de Viagens, Ocorrências do Motorista |
| Comercial | Tabela de Preços Comercial |
| Billing e Assinatura | Onboarding de Conta, Planos, Assinatura do Tenant, Cobrança Recorrente |
| Compliance e Auditoria | Trilha de Auditoria, Gestão de Permissões (RBAC), Logs de Acesso |
| Relatórios e BI | Relatório de Fretes, Relatório Financeiro, Exportação (PDF/Excel/CSV), Dashboard Executivo |
| Comunicação | Alertas Operacionais, Alertas de Manutenção |
| Portais Externos | Landing Page, Cadastro Self-Service |
| Integrações | Integração SEFAZ |
| Configurações da Conta | Dados da Empresa, Timezone e Localidade |
| Armazenamento | Repositório de Anexos |
| Administração da Plataforma | Monitoramento da Plataforma, Gestão de Tenants |

## V2 — Comercialização e mobilidade (37 áreas)

O produto passa a ser vendável em escala (self-service maduro) e a operação ganha o app do
motorista e visibilidade em tempo real.

| Categoria | Itens |
|---|---|
| Cadastros | Rotas Padrão, Praças de Pedágio, Seguradoras |
| Operação | Roteirização |
| Documentos Fiscais | CIOT |
| Financeiro | Apuração por Centro de Custo, DRE, Conciliação Bancária, Repasse a Terceiros |
| Frota e Manutenção | Ciclo de Pneu, Recapagem, Estoque de Peças (Almoxarifado), Licenciamento de Veículo, Seguro de Veículo |
| Motoristas | Avaliação de Motorista |
| Comercial | Simulador de Frete, Carteira de Clientes |
| Billing e Assinatura | Histórico de Faturas, Upgrade/Downgrade de Plano |
| Compliance e Auditoria | Consentimento LGPD, Exportação de Dados do Titular |
| Relatórios e BI | Relatório de Manutenção, Relatório de Motoristas |
| Comunicação | Central de Notificações, Preferências de Canal |
| Suporte | Central de Tickets |
| Portais Externos | Portal do Motorista, Aplicativo Mobile do Motorista, Portal do Cliente |
| Integrações | Integração Mapbox, Integração ANTT/CIOT |
| Rastreamento e Telemetria | Posição em Tempo Real, Histórico de Rota Percorrida |
| Configurações da Conta | Identidade Visual (White-label), Preferências Gerais |
| Administração da Plataforma | Gestão de Planos Globais, Auditoria Cross-tenant |

## V3 — Inteligência e relacionamento (14 áreas)

O produto passa a sugerir, não só registrar — primeiros recursos de IA — e ganha profundidade
comercial (CRM) e de suporte.

| Categoria | Itens |
|---|---|
| Motoristas | Treinamentos |
| Comercial | Funil de Oportunidades, Propostas Comerciais, Contratos de Frete |
| Relatórios e BI | Indicadores Operacionais |
| Inteligência Artificial | Sugestão de Manutenção Preventiva, Precificação Dinâmica Sugerida, Previsão de Prazo de Entrega, Detecção de Anomalias Financeiras |
| Suporte | Chat de Suporte, Base de Conhecimento |
| Rastreamento e Telemetria | Telemetria de Veículo, Geofencing, Alertas de Desvio de Rota |

## V4 — Rede e expansão (6 áreas)

O produto se torna uma plataforma, não só uma ferramenta de uma transportadora isolada.

| Categoria | Itens |
|---|---|
| Comercial | Marketplace de Cargas |
| Inteligência Artificial | Otimização de Rota |
| Integrações | API Pública, Integração GestorPec |
| Workflow e Automação | Fluxos de Aprovação, Automações Configuráveis |

## Horizonte (pós-V4) — 1 área

Depende da maturidade de um produto irmão ainda não iniciado — não faz sentido versionar junto
com V4 (ver [`VISION.md`](./VISION.md), capítulo 21).

| Categoria | Itens |
|---|---|
| Integrações | Integração GestorContábil |

---

## Regra de manutenção deste documento

Toda vez que uma área nova for adicionada em [`PRODUCT_MAP.md`](./PRODUCT_MAP.md), ela recebe uma
versão aqui antes de ser considerada elegível para implementação — nenhuma área é implementada
"fora de versão" só porque parece rápida de fazer.
