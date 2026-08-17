# 001 — Onboarding

## Objetivo

Levar um visitante da Landing Page a uma transportadora operando o GestorFrete, com o mínimo de
fricção possível e sem depender de um vendedor ou técnico — consistente com o Modelo SaaS
self-service (ver [`../product/VISION.md`](../product/VISION.md), capítulo 12). É o único fluxo
que não tem nenhum outro fluxo como pré-requisito: é a porta de entrada do sistema.

## Pré-condições

- O visitante possui CNPJ válido e ativo.
- O visitante possui um meio de pagamento (cartão, PIX ou boleto) — exceto no caminho de Trial.
- Nenhum tenant existe ainda para esse CNPJ (ver Fluxos de exceção para o caso de CNPJ já
  cadastrado).

## Gatilho inicial

O visitante acessa a Landing Page (bounded context `landing`) e escolhe "Começar agora" ou
seleciona um plano diretamente.

## Máquina de Estados — Tenant / Assinatura

```
RASCUNHO
  │
  ├──(escolhe plano pago)──────────► AGUARDANDO_PAGAMENTO
  │                                        │
  │                                        │ (pagamento confirmado via webhook)
  │                                        ▼
  └──(escolhe trial)──────────────► TRIAL ──────────────────────────► ATIVO
                                       │                                 │  ▲
                                       │ (expira sem conversão)          │  │
                                       ▼                                 │  │
                                   SUSPENSO ◄──────────(cobrança falha)──┘  │
                                       │         (tolerância expira)        │
                                       │ ────────────────────► INADIMPLENTE ┤
                                       │                                    │(regulariza)
                                       │(reativação)                       │
                                       └───────────────────────────────────┘
                                       │
                                       │ (tempo máx. de suspensão sem reativação)
                                       ▼
                                   CANCELADO ◄──── CANCELAMENTO_SOLICITADO ◄── (usuário Master solicita, a partir de ATIVO)
                                       │
                                       │ (reativação dentro da política de retenção)
                                       └──────────────────────────────────────► ATIVO
```

Estados: `RASCUNHO`, `AGUARDANDO_PAGAMENTO`, `TRIAL`, `ATIVO`, `INADIMPLENTE`, `SUSPENSO`,
`CANCELAMENTO_SOLICITADO`, `CANCELADO`.

### Transições válidas

| De | Para | Gatilho |
|---|---|---|
| `RASCUNHO` | `AGUARDANDO_PAGAMENTO` | Usuário escolhe plano pago e conclui o cadastro |
| `RASCUNHO` | `TRIAL` | Usuário escolhe iniciar trial gratuito |
| `AGUARDANDO_PAGAMENTO` | `ATIVO` | Webhook Asaas confirma pagamento |
| `AGUARDANDO_PAGAMENTO` | `RASCUNHO` | Pagamento falha e o cadastro expira sem nova tentativa |
| `TRIAL` | `ATIVO` | Usuário assina um plano pago durante ou ao fim do trial |
| `TRIAL` | `SUSPENSO` | Trial expira sem conversão |
| `ATIVO` | `INADIMPLENTE` | Cobrança recorrente falha |
| `INADIMPLENTE` | `ATIVO` | Pagamento regularizado dentro da janela de tolerância |
| `INADIMPLENTE` | `SUSPENSO` | Janela de tolerância expira sem regularização |
| `SUSPENSO` | `ATIVO` | Reativação — pagamento regularizado |
| `SUSPENSO` | `CANCELADO` | Tempo máximo de suspensão atingido sem reativação (política de retenção) |
| `ATIVO` | `CANCELAMENTO_SOLICITADO` | Usuário Master solicita cancelamento (D010 — exige confirmação explícita) |
| `CANCELAMENTO_SOLICITADO` | `CANCELADO` | Fim do ciclo pago corrente é atingido |
| `CANCELAMENTO_SOLICITADO` | `ATIVO` | Usuário desiste do cancelamento antes do fim do ciclo |
| `CANCELADO` | `ATIVO` | Reativação de conta cancelada, dentro da política de retenção de dados |

### Transições inválidas (normativas)

- **Não é permitido** ir de `RASCUNHO` diretamente para `ATIVO` — todo tenant passa por
  `AGUARDANDO_PAGAMENTO` ou `TRIAL`, nunca tem a confirmação de pagamento/trial pulada.
- **Não é permitido** ir de `CANCELADO` diretamente para `SUSPENSO` — uma conta cancelada só
  reativa para `ATIVO`, nunca "meio-reativa" para um estado intermediário.
- **Não é permitido** solicitar cancelamento (`CANCELAMENTO_SOLICITADO`) a partir de `SUSPENSO` ou
  `INADIMPLENTE` — cancelamento voluntário só parte de `ATIVO` ou `TRIAL`; uma conta suspensa segue
  o próprio caminho até `CANCELADO` por tempo, não por solicitação.
- **Não é permitido**, em nenhuma hipótese, excluir fisicamente um tenant em qualquer estado — D001
  (soft delete) aplica-se integralmente mesmo a `CANCELADO`.

### Histórico de Transições

Por D017/D018, o campo de status do tenant nunca é sobrescrito. Cada transição gera um novo
registro em `TenantStatusHistory`: `id`, `tenant_id`, `status`, `usuário` (ou `sistema`, para
transições automáticas como confirmação de webhook), `origem` (ex: `onboarding`, `billing`,
`admin_saas`), `data_hora`, `observação` (obrigatória nas transições para `SUSPENSO`/`CANCELADO`).
Não se aplicam `latitude`/`longitude` a este histórico (campos relevantes apenas a entidades móveis,
como a Viagem — ver [`002-VIAGEM.md`](./002-VIAGEM.md)). Este histórico é a fonte para auditoria de
billing, para o KPI de tempo de onboarding e para investigar disputas de cobrança.

## Fluxo principal

1. **Landing** — visitante conhece o produto e escolhe "Assinar"/"Começar agora" (`landing`).
2. **Escolha do plano** — seleciona o plano por porte de frota/módulos contratados (`pricing`,
   `subscription`).
3. **Cadastro** — preenche dados da empresa (razão social, CNPJ) e do usuário responsável, que se
   tornará o Usuário Master.
4. **Validação de CNPJ** — o sistema valida formato e situação cadastral antes de prosseguir.
5. **Pagamento (Asaas)** — cobrança gerada (cartão, PIX ou boleto conforme plano); sistema aguarda
   confirmação.
6. **Webhook** — Asaas notifica o GestorFrete de forma assíncrona sobre o resultado do pagamento.
7. **Provisionamento** — pagamento confirmado (ou trial iniciado): tenant é criado em `tenancy`,
   plano ativado em `subscription`.
8. **Empresa criada** — tenant existe, isolado por `tenant_id` desde o primeiro registro (D005).
9. **Usuário Master** — o usuário responsável do cadastro é criado com permissão total sobre o
   tenant (ver [`../product/PERSONAS.md`](../product/PERSONAS.md), persona 1 — Diretor).
10. **Primeiro login** — Usuário Master acessa o sistema pela primeira vez.
11. **Assistente de Configuração** — wizard guiado: dados da empresa, timezone, primeira filial,
    convite de outros usuários (`onboarding`, `settings`).
12. **Sistema liberado** — o tenant sai do estado de provisionamento e entra em operação plena
    (`ATIVO` ou `TRIAL`).

## Fluxos alternativos

- **Trial sem cartão**: visitante inicia trial gratuito, pulando Pagamento/Webhook — Provisionamento
  ocorre imediatamente, com prazo de expiração definido pelo plano.
- **Upgrade de plano durante o onboarding**: usuário muda de plano antes de concluir o Assistente de
  Configuração — não reinicia o fluxo, apenas atualiza o plano em `subscription`.
- **Convite de equipe durante o Assistente**: Usuário Master convida outros usuários (Gestor
  Operacional, Financeiro, etc.) antes de finalizar a configuração — não bloqueia a liberação do
  sistema.
- **Onboarding assistido (Enterprise)**: em vez de self-service puro, um Consultor Comercial conduz
  o cadastro e a configuração inicial em nome do prospect, usando acesso temporário e escopado (ver
  [`../product/PERSONAS.md`](../product/PERSONAS.md), persona 12).

## Fluxos de exceção

- **Pagamento recusado (cartão)**: cobrança rejeitada pela operadora → tenant permanece em
  `AGUARDANDO_PAGAMENTO`, usuário é notificado e pode tentar outro meio de pagamento; após N
  tentativas falhas, o cadastro expira (volta a `RASCUNHO`).
- **PIX expirado**: QR Code não pago dentro da janela (ex: 30 minutos) → cobrança expira; o sistema
  permite gerar um novo PIX sem refazer o cadastro.
- **Cartão recusado**: caso específico de pagamento recusado por dados inválidos/limite
  insuficiente — mensagem de erro específica exibida ao usuário (nunca genérica, para permitir
  correção).
- **CNPJ inválido**: falha na validação de formato ou situação cadastral irregular/baixada →
  cadastro bloqueado antes de chegar à etapa de pagamento; usuário orientado a corrigir.
- **CNPJ já cadastrado**: visitante tenta cadastrar um CNPJ que já possui tenant ativo → fluxo
  interrompido com orientação para login ou recuperação de acesso, nunca criação de tenant
  duplicado para o mesmo CNPJ.
- **Webhook não recebido/atrasado**: Asaas confirma o pagamento mas o webhook não chega (falha de
  rede) → uma rotina de conciliação ativa (poll periódico de status junto ao Asaas) evita que o
  tenant fique preso em `AGUARDANDO_PAGAMENTO` indevidamente.
- **Upgrade de plano (pós-ativação)**: usuário contrata mais módulos/porte maior — `subscription`
  atualiza o plano, cobrança proporcional (proration) é gerada; nunca interrompe o acesso do tenant.
- **Downgrade de plano**: aplicado apenas no próximo ciclo de cobrança, nunca retroativamente (evita
  estorno complexo e perda de acesso a dado já lançado sob o plano anterior).
- **Cancelamento**: usuário Master solicita — `CANCELAMENTO_SOLICITADO` com carência até o fim do
  ciclo pago; nunca cancelamento imediato sem confirmação explícita (D010).
- **Reativação**: tenant `SUSPENSO` ou `CANCELADO` retoma o pagamento → volta a `ATIVO`; dados
  preservados integralmente (D001 — nunca foram excluídos fisicamente).
- **Trial expirado sem conversão**: chega ao prazo sem pagamento → `SUSPENSO` (nunca `CANCELADO`
  diretamente), com janela de graça antes de qualquer arquivamento de dado.

## Eventos publicados

| Evento | Gerado quando |
|---|---|
| `TenantProvisionado` | Tenant sai de `RASCUNHO`/`AGUARDANDO_PAGAMENTO`/`TRIAL` e é criado em `tenancy` |
| `AssinaturaCriada` | Plano é ativado pela primeira vez (`ATIVO` ou `TRIAL`) — já catalogado em [`../product/EVENT_MAP.md`](../product/EVENT_MAP.md) |
| `PlanoAlterado` | Upgrade/downgrade de plano — já catalogado em `EVENT_MAP.md` |
| `CobrancaRealizada` | Cobrança recorrente processada com sucesso — já catalogado em `EVENT_MAP.md` |
| `CobrancaFalhou` | Cobrança recorrente falha — já catalogado em `EVENT_MAP.md` |
| `TenantSuspenso` | Tenant transita para `SUSPENSO` (trial expirado ou inadimplência não regularizada) |
| `AssinaturaCancelada` | Tenant transita para `CANCELAMENTO_SOLICITADO` ou `CANCELADO` |
| `TenantReativado` | Tenant transita de `SUSPENSO`/`CANCELADO` de volta para `ATIVO` |

## Eventos consumidos

Nenhum — este é o fluxo de entrada do sistema; ele não reage a eventos de outros bounded contexts.

## Permissões

| Etapa | Quem executa |
|---|---|
| Landing, Cadastro, Pagamento | Visitante anônimo (sem conta ainda) |
| Provisionamento | Sistema (automático, disparado pelo webhook confirmado) |
| Primeiro Login, Assistente de Configuração | Usuário Master do tenant recém-criado |
| Onboarding assistido | Consultor Comercial, com acesso temporário e escopado ao tenant do prospect |
| Suspensão/reativação/cancelamento forçados (casos excepcionais) | Administrador SaaS, sempre com justificativa auditada |

## Auditoria

Toda transição de estado do tenant (`TenantProvisionado`, `TenantSuspenso`, `AssinaturaCancelada`,
`TenantReativado`) e toda alteração de plano é registrada na trilha de auditoria (`audit`), com
ator (usuário, sistema automático ou Administrador SaaS), timestamp e motivo quando aplicável — D007.

## Notificações

- E-mail de boas-vindas após o Provisionamento.
- Notificação de pagamento recusado / PIX expirado, com ação de correção.
- Lembrete de trial expirando (antes de virar `SUSPENSO`).
- Confirmação de cancelamento, com a data em que passa a valer.
- Confirmação de reativação.

## Capacidades Transversais

1. **Timeline Universal** (D022): `TenantStatusHistory` completo + eventos de cobrança
   (`CobrancaRealizada`/`CobrancaFalhou`) + comentários internos + anexos.
2. **Comentários** (D023): aplicável — uso interno da equipe GestorFrete (Consultor Comercial,
   Implantação, Suporte) sobre o tenant; nunca visível ao próprio tenant.
3. **Anexos** (D024): comprovante de pagamento, contrato assinado (planos Enterprise negociados).
4. **Favoritos** (D025): não se aplica à entidade Tenant em si (o usuário do tenant não "favorita"
   sua própria conta); aplica-se a telas do painel da equipe GestorFrete (ex: "tenants em trial
   expirando esta semana" como filtro favoritável pelo Administrador SaaS).
5. **Pesquisa Global** (D026): razão social, CNPJ, nome e e-mail do Usuário Master.

## Regras de negócio relacionadas

- D001 — soft delete: tenant `CANCELADO` nunca é excluído fisicamente.
- D005/D006 — `tenant_id` obrigatório desde a criação; isolamento lógico, não schema-per-tenant.
- D010 — nenhuma operação crítica (cancelamento) sem confirmação explícita do usuário.
- D015/D016 — este fluxo é a referência viva dessas duas decisões.
- D017/D018 — histórico de transições via `TenantStatusHistory`.
- D022–D026 — capacidades transversais aplicadas na seção acima.

## SLA

| Etapa | Prazo |
|---|---|
| Validação de CNPJ | Imediato (síncrono, na submissão do cadastro) |
| Confirmação de pagamento (webhook) | Até 5 minutos; acima disso, entra na rotina de conciliação ativa |
| Provisionamento do tenant após pagamento confirmado | Imediato (automático) |
| Expiração de PIX não pago | 30 minutos |
| Tolerância de inadimplência antes de `SUSPENSO` | A definir (depende da política comercial por plano) |
| Carência de `CANCELAMENTO_SOLICITADO` até `CANCELADO` | Até o fim do ciclo pago corrente |
| Janela de graça de dado após `SUSPENSO`/`CANCELADO` antes de arquivamento | A definir |

## Indicadores Gerados

O Onboarding gera, para BI/analytics:

- Tempo total de onboarding (Landing → Sistema Liberado)
- Taxa de conversão por etapa (funil: Landing → Cadastro → Pagamento → Ativo)
- Taxa de conversão de Trial em plano pago
- Taxa de abandono por motivo (CNPJ inválido, pagamento recusado, PIX expirado)
- Churn por inadimplência não regularizada
- Receita nova por período (novas assinaturas)
- Tempo médio de resposta do webhook Asaas

## Riscos

- Pagamento confirmado no Asaas, mas webhook nunca chega (inconsistência entre provedor e sistema).
- CNPJ com situação cadastral alterada após a validação inicial (ex: baixado meses depois).
- Usuário Master perde acesso (esquece credenciais) sem processo de recuperação definido ainda.
- Abuso de Trial (múltiplos trials para o mesmo CNPJ/grupo econômico via cadastros levemente
  distintos).
- Cobrança duplicada em caso de reprocessamento de webhook.

## KPIs impactados

- Ativação: tempo entre cadastro e primeiro frete despachado (ver
  [`../product/VISION.md`](../product/VISION.md), capítulo 32).
- Taxa de conversão de trial em plano pago.
- Tempo total de onboarding (Landing → Sistema Liberado).
- Churn por falha de pagamento não regularizada.

## Critérios de encerramento

- **Sucesso**: tenant atinge `ATIVO` (ou `TRIAL`) com o Assistente de Configuração concluído —
  "Sistema Liberado".
- **Sem sucesso**: cadastro expira em `RASCUNHO`/`AGUARDANDO_PAGAMENTO` por inatividade, ou trial
  expira sem conversão e o tenant permanece `SUSPENSO` além da janela de graça.

## Pontos de integração

- **Asaas** — geração de cobrança e recebimento de webhook de pagamento.
- **Validador de CNPJ** — Receita Federal ou provedor terceiro de consulta de situação cadastral.
- Bounded contexts: `landing`, `onboarding`, `tenancy`, `subscription`, `billing`, `pricing`,
  `identity_access`, `settings`.

## Requisitos futuros

- Ambiente sandbox dedicado para demonstrações do Consultor Comercial, isolado de tenants reais.
- Suporte a múltiplos meios de pagamento simultâneos por tenant.
- Onboarding via canais/parcerias (contadores, cooperativas do agronegócio — ver
  [`../product/VISION.md`](../product/VISION.md), capítulo 14).
