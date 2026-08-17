# 010 — Administração (Plataforma)

Entidades da camada SaaS do GestorFrete — a base sobre a qual todo o resto do sistema opera.
Template completo de 22 campos (ver [`README.md`](./README.md)). Organizado nos seis blocos
sugeridos: Plataforma SaaS, Identidade, Segurança, Configurações, Personalização, Administração da
Plataforma.

## Dois princípios que atravessam o documento inteiro

- **D141 — Configuração é centralizada**: toda configuração do sistema pertence a este módulo
  (`settings`/`tenancy`/`subscription`/`billing`, conforme o bloco); os demais bounded contexts
  apenas consultam por referência, nunca duplicam ou definem a sua própria. Já era praticado
  informalmente (a alçada de aprovação em `004-manutencao.md`, a numeração fiscal em
  `007-fiscal.md`) — agora tem entidade própria aqui (`Parâmetro do Tenant`) em vez de ficar
  apenas prometido como "a ser detalhado".
- **D142 — Administração configura, nunca executa regra operacional**: este módulo nunca decide,
  por exemplo, se uma Ordem de Serviço específica precisa de aprovação — ele só guarda o valor da
  alçada. Quem decide e executa é sempre o bounded context operacional dono da regra
  (`maintenance`, no exemplo).

## Reconciliação (D076) — antes de criar qualquer coisa

Duas reconciliações importantes, nos dois sentidos:

1. **Não recriado** (já existe): `Usuário`, `Papel` (= "Perfil" pedido no bloco Identidade — mesmo
   conceito, nome já estabelecido por D028), `Permissão`, `Filial` — todos já documentados em
   [`001-cadastros.md`](./001-cadastros.md), donos de `identity_access`/`tenancy`. Este arquivo os
   referencia, nunca os redefine.
2. **Placeholder original não coberto por este lote**: `ENTITY_CATALOG.md` também listava `Ticket de
   Suporte`, `Interação do Ticket` e `Atribuição de Consultor Comercial` para esta categoria — nenhum
   dos seis blocos pedidos nesta rodada os menciona (eles pertencem ao bounded context `support`,
   conceitualmente distante de Plataforma SaaS/Identidade/Segurança/Configurações/Personalização/
   Administração). Não removidos nem inventados agora — adiados explicitamente para quando `support`
   for o foco de um lote, em vez de forçados aqui só para "fechar" o placeholder original.
3. **Consolidações dentro do próprio pedido**: "Timezone"/"Fuso" são o mesmo conceito (fuso horário),
   uma única entidade; "Empresa" é o próprio `Tenant`, não uma entidade separada; "Licenciamento" é o
   que `Assinatura`/`Plano` já cobrem, não duplicado; "Logs" e "Auditoria" (bloco Segurança) são o
   mesmo conceito — uma única entidade `Log de Auditoria`; "White Label" (bloco 1) é uma feature
   habilitada via `Item de Plano`/`Recurso Habilitado do Tenant` (bloco 6), cujo conteúdo de fato
   (logo, cores, tema) vive em `Configuração de Personalização` (bloco 5) — três blocos citam o
   mesmo recurso de ângulos diferentes, não três entidades.

Resultado: **20 entidades novas** nesta categoria.

---

# Bloco 1 — Plataforma SaaS

## Tenant

- **Objetivo**: Representa a transportadora cliente do GestorFrete — a raiz de todo isolamento
  multi-tenant (D005/D006) e o próprio "Empresa" mencionado no pedido (não uma entidade separada).
- **Responsabilidades**: Ser a fronteira de isolamento de dados de todo o sistema; possuir uma
  Assinatura vigente; ser o escopo de toda configuração (D141).
- **O que não faz**: Não executa nenhuma regra operacional (D142) — apenas existe como contexto para
  todas as demais entidades do sistema.
- **Aggregate Root**: Sim — o aggregate root de mais alto nível de todos (todas as demais entidades
  do sistema, direta ou indiretamente, pertencem a um Tenant, exceto Platform Reference Data, D046).
- **Bounded Context proprietário**: `tenancy`
- **Principais relacionamentos**: Assinatura (1:1 vigente); Filial (1:N,
  [`001-cadastros.md`](./001-cadastros.md)); todas as demais entidades do sistema (por
  `tenant_id`, D005).
- **Eventos que publica**: `TenantCriado`, `TenantSuspenso`, `TenantReativado` (novos).
- **Eventos que consome**: `AssinaturaCancelada` (`subscription`) — pode disparar suspensão.
- **Invariantes**: CNPJ único na plataforma (não por tenant — é o próprio identificador do tenant);
  um Tenant suspenso bloqueia login de todos os seus Usuários, mas nunca exclui dados (D001).
- **Regras de negócio associadas**: D001, D005/D006, D141.
- **Estados**: `Trial` / `Ativo` / `Suspenso` / `Cancelado`.
- **Auditoria**: D007 — mudança de status do Tenant é auditoria de plataforma (visível ao Auditor
  Interno, D051-D062, não ao Auditor do próprio tenant).
- **Linha do tempo (Timeline Universal)**: criação, mudanças de plano, suspensões/reativações.
- **Anexos suportados**: contrato assinado (D024).
- **Comentários suportados**: Sim, uso interno da equipe GestorFrete (D023).
- **KPIs relacionados**: churn, tempo médio em trial até conversão (calculados em `analytics`,
  D090).
- **Documentos canônicos relacionados**: Nenhum ainda — candidato natural a um
  `docs/flows/011-ONBOARDING.md` revisado (já existe `001-ONBOARDING.md`, a cruzar).
- **Evoluções futuras previstas**: hierarquia de tenants (holding com múltiplas transportadoras) —
  fora do escopo desta fundação.
- **Dependências obrigatórias**: Nenhuma — é a raiz.
- **Dependências proibidas**: Nenhuma restrição — é referenciado por todos, não o contrário.
- **Dono da Timeline**: Aggregate Tenant (este próprio).
- **Capacidade Offline**: Não.

## Plano

- **Objetivo**: Catálogo dos planos comerciais oferecidos (ex: Básico/Profissional/Enterprise).
- **Responsabilidades**: Definir preço base e ser composto por Itens de Plano (features/limites).
- **O que não faz**: Não decide quais features um Tenant específico tem habilitadas no dia a dia —
  isso é `Recurso Habilitado do Tenant` (Bloco 6), que parte do Plano mas permite exceção pontual.
- **Aggregate Root**: Sim — entidade de **Referência** (D036).
- **Bounded Context proprietário**: `subscription`
- **Principais relacionamentos**: Item de Plano (1:N); Assinatura (1:N).
- **Eventos que publica**: `PlanoCadastrado`, `PlanoDescontinuado` (novos).
- **Eventos que consome**: Nenhum.
- **Invariantes**: nome único na plataforma; um Plano descontinuado não aceita novas Assinaturas,
  mas mantém as existentes (D001).
- **Regras de negócio associadas**: D001, D005/D006 (exceção: Plano é Platform Reference Data,
  D046 — sem `tenant_id`, compartilhado entre todos os tenants).
- **Estados**: `Ativo` / `Descontinuado`.
- **Auditoria**: D007.
- **Linha do tempo**: cadastro, alterações de preço.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: distribuição de tenants por plano (dado bruto, `analytics`).
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: planos customizados por negociação (Enterprise sob medida).
- **Dependências obrigatórias**: Nenhuma.
- **Dependências proibidas**: Cliente, Viagem, CT-e, Financeiro do tenant (é Platform Reference
  Data, D046 — nunca lê dado de um tenant específico).
- **Dono da Timeline**: Aggregate Plano (este próprio).
- **Capacidade Offline**: Consulta Offline.

## Item de Plano

- **Objetivo**: Uma feature ou limite específico incluído em um Plano (ex: "até 20 veículos",
  "módulo de rastreamento incluído", "White Label habilitado").
- **Responsabilidades**: Ser a origem-catálogo do que `Recurso Habilitado do Tenant` (Bloco 6) ativa
  por padrão para um Tenant naquele Plano.
- **O que não faz**: Não força a habilitação — um Tenant pode ter uma exceção pontual (upgrade
  temporário) registrada em `Recurso Habilitado do Tenant`, sem mudar de Plano.
- **Aggregate Root**: Não — parte do agregado Plano.
- **Bounded Context proprietário**: `subscription`
- **Principais relacionamentos**: Plano (N:1).
- **Eventos que publica**: Nenhum diretamente.
- **Eventos que consome**: Nenhum.
- **Invariantes**: chave do item única dentro do mesmo Plano.
- **Regras de negócio associadas**: D005/D006 (D046 — Platform Reference Data).
- **Estados**: Não aplicável.
- **Auditoria**: D007.
- **Linha do tempo**: parte do Plano.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: Nenhuma isolada.
- **Dependências obrigatórias**: Plano.
- **Dependências proibidas**: Cliente, Viagem, CT-e, Financeiro do tenant.
- **Dono da Timeline**: Aggregate Plano.
- **Capacidade Offline**: Consulta Offline.

## Assinatura

- **Objetivo**: Representa o vínculo comercial vigente entre um Tenant e um Plano.
- **Responsabilidades**: Controlar o ciclo trial → ativa → cancelada; disparar Cobrança Recorrente.
- **O que não faz**: Não processa o pagamento em si — isso é Cobrança Recorrente.
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `subscription`
- **Principais relacionamentos**: Tenant (1:1 vigente); Plano (N:1); Cobrança Recorrente (1:N).
- **Eventos que publica**: `AssinaturaIniciada`, `AssinaturaRenovada`, `AssinaturaCancelada`,
  `TrialExpirado` (novos).
- **Eventos que consome**: Nenhum.
- **Invariantes**: um Tenant tem no máximo uma Assinatura `Ativa` por vez; trial tem prazo definido,
  após o qual converte ou expira automaticamente.
- **Regras de negócio associadas**: D001, D005/D006.
- **Estados**: `Trial` / `Ativa` / `Cancelada` / `Suspensa` (inadimplência).
- **Auditoria**: D007.
- **Linha do tempo**: início, renovações, cancelamento.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Sim, negociação comercial (D023).
- **KPIs relacionados**: MRR, churn, taxa de conversão trial→pago (calculados em `analytics`, D090).
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: upgrade/downgrade de plano com proration automático.
- **Dependências obrigatórias**: Tenant, Plano.
- **Dependências proibidas**: CT-e, Pneu, Ordem de Serviço.
- **Dono da Timeline**: Aggregate Assinatura (este próprio).
- **Capacidade Offline**: Não.

## Cobrança Recorrente

- **Objetivo**: Registro de cada cobrança periódica (mensal/anual) gerada por uma Assinatura.
- **Responsabilidades**: Guardar valor, data de vencimento, status de pagamento.
- **O que não faz**: Não é o mesmo que Fatura/Conta a Receber do módulo Financeiro
  ([`006-financeiro.md`](./006-financeiro.md)) — aquele é o financeiro **do tenant** (frete que ele
  cobra do cliente dele); este é o financeiro **da plataforma** (o que o GestorFrete cobra do
  tenant) — dois níveis completamente distintos, nunca confundidos.
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `billing`
- **Principais relacionamentos**: Assinatura (N:1).
- **Eventos que publica**: `CobrancaGerada`, `CobrancaPaga`, `CobrancaFalhou` (novos).
- **Eventos que consome**: Nenhum.
- **Invariantes**: valor maior que zero; uma Cobrança `Falhou` gera nova tentativa configurável antes
  de suspender a Assinatura.
- **Regras de negócio associadas**: D001, D097 (valor, moeda BRL D075, momento da cobrança), D100
  (imutável após conciliada).
- **Estados**: `Pendente` / `Paga` / `Falhou` / `Cancelada`.
- **Auditoria**: D007.
- **Linha do tempo**: parte da Assinatura.
- **Anexos suportados**: recibo/nota fiscal da plataforma (D024).
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: taxa de inadimplência de plataforma (distinta da inadimplência de clientes
  do tenant, calculada em `analytics`).
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: múltiplos gateways de cobrança (cartão, boleto, PIX).
- **Dependências obrigatórias**: Assinatura.
- **Dependências proibidas**: Cliente do tenant, Viagem, CT-e, Financeiro do tenant.
- **Dono da Timeline**: Aggregate Assinatura.
- **Capacidade Offline**: Não.

---

# Bloco 2 — Identidade

## Grupo de Usuários

- **Objetivo**: Agrupa Usuários para fins organizacionais (ex: "Filial Norte", "Equipe Noturna"),
  independente de Papel/Permissão.
- **Responsabilidades**: Ser referenciado por filtros e notificações em massa.
- **O que não faz**: Não define permissão — isso é exclusivamente Papel/Permissão
  (`001-cadastros.md`, D051-D062); Grupo é puramente organizacional, nunca uma segunda via de RBAC
  (evita o erro clássico de dois sistemas de autorização coexistindo).
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `identity_access`
- **Principais relacionamentos**: Usuário (N:N).
- **Eventos que publica**: `GrupoDeUsuariosCriado` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: nome único por tenant.
- **Regras de negócio associadas**: D001, D005/D006.
- **Estados**: `Ativo` / `Inativo`.
- **Auditoria**: D007.
- **Linha do tempo**: criação, alterações de membros.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: Nenhuma prevista.
- **Dependências obrigatórias**: Nenhuma.
- **Dependências proibidas**: Cliente, CT-e, Financeiro, Pneu, Viagem.
- **Dono da Timeline**: Aggregate Grupo de Usuários (este próprio).
- **Capacidade Offline**: Consulta Offline.

## Convite

- **Objetivo**: Registra o convite pendente para uma pessoa se tornar Usuário de um Tenant.
- **Responsabilidades**: Guardar e-mail, Papel proposto, prazo de validade.
- **O que não faz**: Não cria o Usuário sozinho — apenas ao ser aceito, dispara a criação.
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `identity_access`
- **Principais relacionamentos**: Papel proposto (referenciado, `001-cadastros.md`); Usuário
  resultante (0..1, após aceite).
- **Eventos que publica**: `ConviteEnviado`, `ConviteAceito`, `ConviteExpirado`,
  `ConviteRevogado` (novos).
- **Eventos que consome**: Nenhum.
- **Invariantes**: e-mail único por Convite pendente no mesmo tenant; expira após prazo configurável.
- **Regras de negócio associadas**: D001, D005/D006, D010 (aceite é confirmação explícita).
- **Estados**: `Pendente` / `Aceito` / `Expirado` / `Revogado`.
- **Auditoria**: D007.
- **Linha do tempo**: envio, aceite/expiração/revogação.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: taxa de aceite de convite (dado bruto, `analytics`).
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: convite em lote (importação de planilha).
- **Dependências obrigatórias**: Papel.
- **Dependências proibidas**: Cliente, CT-e, Financeiro, Pneu, Viagem.
- **Dono da Timeline**: Aggregate Convite (este próprio).
- **Capacidade Offline**: Não.

## Fator de Autenticação

- **Objetivo**: Preparação para múltiplos fatores de autenticação (MFA) além de senha — TOTP,
  SMS, e-mail, biometria (mobile, já antecipado em `009-app_motorista.md`, `SESSAO_MOBILE.METODO_AUTENTICACAO`).
- **Responsabilidades**: Guardar quais fatores um Usuário tem habilitados.
- **O que não faz**: **Preparação, não implementação completa** desta rodada — a validação em si
  (envio de código, verificação TOTP) é infraestrutura futura; o modelo já existe para não exigir
  migração estrutural quando for implementado (mesmo princípio de D120 aplicado à autenticação).
- **Aggregate Root**: Não — parte do agregado Usuário.
- **Bounded Context proprietário**: `identity_access`
- **Principais relacionamentos**: Usuário (N:1).
- **Eventos que publica**: `FatorDeAutenticacaoHabilitado`, `FatorDeAutenticacaoDesabilitado`
  (novos).
- **Eventos que consome**: Nenhum.
- **Invariantes**: um Usuário pode ter múltiplos fatores habilitados simultaneamente (D128-style —
  não assume um único fator).
- **Regras de negócio associadas**: D005/D006.
- **Estados**: `Ativo` / `Inativo`.
- **Auditoria**: D007 — habilitar/desabilitar MFA é sensível.
- **Linha do tempo**: habilitação, desabilitação.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: percentual de usuários com MFA habilitado (dado bruto, `analytics`).
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: implementação completa de TOTP/SMS — hoje só o modelo existe.
- **Dependências obrigatórias**: Usuário.
- **Dependências proibidas**: Cliente, CT-e, Financeiro, Pneu, Viagem.
- **Dono da Timeline**: Aggregate Usuário.
- **Capacidade Offline**: Não.

---

# Bloco 3 — Segurança

## Sessão de Acesso (Web/Portal)

- **Objetivo**: Equivalente de Sessão Mobile ([`009-app_motorista.md`](./009-app_motorista.md)) para
  acessos via navegador/portal web — mesma disciplina D140 (nunca representa identidade, só quem/
  onde/quando).
- **Responsabilidades**: Autenticar sessão web; expirar por inatividade; permitir revogação
  administrativa.
- **O que não faz**: Não cacheia permissão (D060, mesmo princípio de Sessão Mobile — autorização
  sempre resolvida ao vivo).
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `identity_access`
- **Principais relacionamentos**: Usuário (N:1).
- **Eventos que publica**: `SessaoDeAcessoIniciada`, `SessaoDeAcessoEncerrada` (novos).
- **Eventos que consome**: Nenhum.
- **Invariantes**: expira por inatividade (prazo configurável via Parâmetro do Tenant, D141);
  revogação nunca implica bloqueio do Usuário — são independentes (mesmo princípio de D132).
- **Regras de negócio associadas**: D027, D060, D132, D140.
- **Estados**: `Ativa` / `Expirada` / `Encerrada`.
- **Auditoria**: D007.
- **Linha do tempo**: início, encerramento.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: MFA obrigatório para sessões administrativas sensíveis.
- **Dependências obrigatórias**: Usuário.
- **Dependências proibidas**: Cliente, CT-e, Financeiro, Pneu, Viagem.
- **Dono da Timeline**: Aggregate Sessão de Acesso (este próprio).
- **Capacidade Offline**: Não.

## Token de API

- **Objetivo**: Representa uma credencial de longa duração para integrações servidor-a-servidor
  (distinta de uma Sessão de usuário humano).
- **Responsabilidades**: Autenticar chamadas de integração; ser revogável a qualquer momento.
- **O que não faz**: Não concede permissão além do RBAC do Usuário técnico ao qual pertence — nunca
  um caminho paralelo de autorização (D061 — nenhuma API bypassa o RBAC).
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `identity_access`
- **Principais relacionamentos**: Usuário técnico (N:1, um Usuário de sistema dedicado à integração,
  não uma pessoa).
- **Eventos que publica**: `TokenDeApiCriado`, `TokenDeApiRevogado` (novos).
- **Eventos que consome**: Nenhum.
- **Invariantes**: valor do token nunca reaproveitado (D084); revogação é imediata e definitiva —
  nunca reativado, um novo token é sempre emitido.
- **Regras de negócio associadas**: D061, D084.
- **Estados**: `Ativo` / `Revogado`.
- **Auditoria**: D007 — criação/revogação de token é sensível.
- **Linha do tempo**: criação, uso (último uso, D081 projeção), revogação.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Sim, finalidade do token (D023).
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: escopo granular por token (ex: só leitura, só um bounded
  context).
- **Dependências obrigatórias**: Usuário técnico.
- **Dependências proibidas**: Cliente, CT-e, Financeiro, Pneu, Viagem diretamente.
- **Dono da Timeline**: Aggregate Token de API (este próprio).
- **Capacidade Offline**: Não.

## Bloqueio de Acesso

- **Objetivo**: Registra o bloqueio de acesso de um Usuário — automático (tentativas de login
  falhas consecutivas) ou administrativo (decisão de um Gestor/Administrador).
- **Responsabilidades**: Impedir novo login enquanto vigente; guardar motivo e ator.
- **O que não faz**: Não substitui `Motorista.STATUS_APTIDAO`
  ([`001-cadastros.md`](./001-cadastros.md)) — aquele é sobre aptidão para dirigir/operar; este é
  puramente sobre acesso ao sistema. Os dois podem coexistir sem relação direta.
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `identity_access`
- **Principais relacionamentos**: Usuário (N:1).
- **Eventos que publica**: `BloqueioDeAcessoAplicado`, `BloqueioDeAcessoRemovido` (novos).
- **Eventos que consome**: Nenhum.
- **Invariantes**: motivo obrigatório para bloqueio administrativo (D010); bloqueio automático por
  tentativas falhas é temporário e configurável, distinto do administrativo (indefinido até remoção
  explícita).
- **Regras de negócio associadas**: D007, D010.
- **Estados**: `Vigente` / `Removido`.
- **Auditoria**: D007.
- **Linha do tempo**: aplicação, remoção.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Sim, justificativa (D023).
- **KPIs relacionados**: taxa de bloqueio por tentativas falhas (possível indício de ataque —
  calculado em `analytics`).
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: bloqueio automático por geolocalização suspeita.
- **Dependências obrigatórias**: Usuário.
- **Dependências proibidas**: Cliente, CT-e, Financeiro, Pneu, Viagem.
- **Dono da Timeline**: Aggregate Usuário (via referência).
- **Capacidade Offline**: Não.

## Log de Auditoria

- **Objetivo**: Formaliza como entidade própria o que D007 vinha citando como princípio desde a
  primeira decisão do projeto — o registro de auditoria de qualquer ação sensível em qualquer
  bounded context. Consolida "Auditoria" e "Logs" (pedidos separadamente no Bloco 3) em uma única
  entidade — são o mesmo conceito.
- **Responsabilidades**: Ser o destino de todo evento de auditoria publicado por qualquer bounded
  context (D007); nunca interpretar o conteúdo, apenas registrá-lo com fidelidade.
- **O que não faz**: Não decide o que é ou não auditável — isso já está definido em cada entidade
  desde sua concepção (a coluna "Auditoria" de cada uma, em todos os arquivos de domínio já
  escritos); este é o repositório, não a regra.
- **Aggregate Root**: Sim — entidade **Histórica** (D037) por definição, alto volume.
- **Bounded Context proprietário**: `audit`
- **Principais relacionamentos**: Qualquer entidade do sistema (referência polimórfica —
  `ENTIDADE_TIPO` + `ENTIDADE_ID`, mesmo padrão de `Evento Fiscal`/`Assinatura Digital`).
- **Eventos que publica**: Nenhum — é o destino final, não a origem.
- **Eventos que consome**: Todo evento de domínio marcado como auditável em qualquer bounded context
  (D008 — consome por evento, nunca lê a tabela de outro módulo diretamente).
- **Invariantes**: nunca editado nem apagado, sob nenhuma circunstância, mesmo por Administrador
  SaaS (D001/D037/D109 — reforço máximo, é a própria garantia de integridade do sistema); **nunca
  depende da existência contínua do ator que o gerou (D147)** — guarda um snapshot do identificador
  do ator (nome, papel no momento) além da referência por ID, mesmo princípio de Snapshot já usado
  em `VIAGEM.NOME_MOTORISTA_SNAPSHOT` (D038/D071) — se o Usuário for removido depois (soft delete,
  D001), o Log de Auditoria não perde significado.
- **Regras de negócio associadas**: D007 (agora com entidade própria), D037, D109, D147 (snapshot do
  ator, D038).
- **Estados**: Não aplicável.
- **Auditoria**: Ele mesmo é o mecanismo de auditoria.
- **Linha do tempo**: consumida por todas as entidades, por referência.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: Nenhum direto — é a fonte bruta para qualquer indicador de compliance.
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: armazenamento em cold storage após período de retenção ativa (ver
  [`../information-model/007-DATA_RETENTION.md`](../information-model/007-DATA_RETENTION.md)).
- **Dependências obrigatórias**: Nenhuma específica — depende de eventos de todos os bounded
  contexts.
- **Dependências proibidas**: Nenhuma — por natureza, é o único agregado com permissão de "saber
  sobre" todos os outros, mas apenas como espectador (D008), nunca como participante ativo.
- **Dono da Timeline**: Não aplicável — ele é a fonte, não o consumidor, de timeline.
- **Capacidade Offline**: Não.

---

# Bloco 4 — Configurações

## Configuração Regional do Tenant

- **Objetivo**: Fuso horário ("Timezone"/"Fuso" — mesmo conceito, uma entidade), idioma e moeda
  padrão do Tenant.
- **Responsabilidades**: Ser consultada por qualquer entidade que precise formatar data/hora, texto
  ou valor monetário na experiência do usuário daquele tenant.
- **O que não faz**: Não altera a moeda de registros já gravados (D075 — BRL é o padrão de
  persistência hoje; esta configuração afeta apresentação/futuro multi-moeda, não o passado).
- **Aggregate Root**: Sim — um registro por Tenant.
- **Bounded Context proprietário**: `settings`
- **Principais relacionamentos**: Tenant (1:1).
- **Eventos que publica**: `ConfiguracaoRegionalAtualizada` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: um único registro `Ativo` por Tenant.
- **Regras de negócio associadas**: D005/D006, D141, D074 (granularidade de exibição segue o fuso
  aqui definido).
- **Estados**: Não aplicável — é configuração simples.
- **Auditoria**: D007.
- **Linha do tempo**: alterações.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: suporte a múltiplas moedas operacionais simultâneas (D075 já
  antecipa o campo).
- **Dependências obrigatórias**: Tenant.
- **Dependências proibidas**: Cliente, CT-e, Financeiro, Pneu, Viagem.
- **Dono da Timeline**: Aggregate Configuração Regional do Tenant (este próprio).
- **Capacidade Offline**: Consulta Offline.

## Configuração de Numeração

- **Objetivo**: Formaliza, como entidade própria, o que D029/D030 já prometia desde o Modelo de
  Domínio — o formato de código funcional configurável por tenant para cada tipo de entidade (ex:
  Viagem, Ordem de Serviço) que **não** seja documento fiscal (CT-e/MDF-e já tem sua própria
  numeração exclusiva em `Configuração Fiscal do Tenant`, [`007-fiscal.md`](./007-fiscal.md), D110 —
  não duplicada aqui).
- **Responsabilidades**: Definir prefixo, quantidade de dígitos, próximo número por tipo de
  entidade.
- **O que não faz**: Não define numeração fiscal (D110, exclusivo de `documents`).
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `settings`
- **Principais relacionamentos**: Tenant (N:1 — um registro por tipo de entidade configurável).
- **Eventos que publica**: `ConfiguracaoDeNumeracaoAtualizada` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: próximo número nunca decresce nem é reutilizado (D084), mesmo princípio de
  `CONFIGURACAO_FISCAL.PROXIMO_NUMERO_CTE`.
- **Regras de negócio associadas**: D029/D030, D084, D141.
- **Estados**: `Ativa` / `Inativa`.
- **Auditoria**: D007.
- **Linha do tempo**: alterações de formato.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: numeração por Filial (série distinta por unidade).
- **Dependências obrigatórias**: Tenant.
- **Dependências proibidas**: Cliente, CT-e (tem a sua própria), Financeiro, Pneu.
- **Dono da Timeline**: Aggregate Configuração de Numeração (este próprio).
- **Capacidade Offline**: Consulta Offline.

## Parâmetro do Tenant

- **Objetivo**: A peça que fecha o ciclo aberto em `004-manutencao.md` (Alçada de Aprovação) e
  `009-app_motorista.md` (Evidência de Conclusão Exigida) — um parâmetro de configuração genérico,
  de posse deste módulo (D141), consultado por qualquer bounded context operacional, nunca
  duplicado.
- **Responsabilidades**: Guardar pares chave/valor de configuração de negócio (ex:
  `ALCADA_APROVACAO_MANUTENCAO`, `EVIDENCIA_CONCLUSAO_EXIGIDA`, futuros parâmetros ainda não
  antecipados) — vocabulário de chaves extensível (D120-style), nunca uma coluna nova por parâmetro.
- **O que não faz**: Não decide o efeito de negócio do parâmetro (D142) — só o guarda; quem decide é
  sempre o bounded context operacional consultando o valor.
- **Aggregate Root**: Sim — entidade **Histórica** (D037/D143): uma mudança de valor nunca
  sobrescreve o registro anterior, gera um novo.
- **Bounded Context proprietário**: `settings`
- **Principais relacionamentos**: Tenant (N:1); consultado por `maintenance`, `mobile` e qualquer
  outro bounded context que precise de um parâmetro configurável, sempre por leitura (D008).
- **Eventos que publica**: `ParametroDoTenantAtualizado` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: chave única por Tenant **vigente** (D144 — pode haver múltiplos registros da
  mesma chave com vigências não sobrepostas, mas apenas um vigente em cada instante); tipo de valor
  (Monetário/Booleano/Inteiro/Texto) declarado junto à chave, para o consumidor nunca precisar
  adivinhar; todo parâmetro distingue Valor Padrão da Plataforma (herdado, não editável pelo tenant)
  de Valor Sobrescrito pelo Tenant (opcional) no mesmo registro — nunca dois registros para
  representar isso (D145); o valor efetivo é a sobrescrita quando presente, senão o padrão.
- **Regras de negócio associadas**: D141, D142, D120 (vocabulário de chaves extensível), D143
  (histórico), D144 (vigência), D145 (padrão × sobrescrita).
- **Estados**: Não aplicável.
- **Auditoria**: D007 — alteração de parâmetro que afeta regra operacional (ex: alçada) é sensível.
- **Linha do tempo**: alterações de valor (cada uma um novo registro histórico, D143).
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Sim, justificativa de mudança (D023).
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: `004-manutencao.md` (Alçada de Aprovação),
  `009-app_motorista.md` (Evidência de Conclusão Exigida) — primeiros consumidores já documentados.
- **Evoluções futuras previstas**: parâmetros por Filial/Categoria de Veículo, não só por Tenant
  inteiro.
- **Dependências obrigatórias**: Tenant.
- **Dependências proibidas**: Cliente, CT-e, Pneu — nunca guarda dado transacional, só
  configuração.
- **Dono da Timeline**: Aggregate Parâmetro do Tenant (este próprio).
- **Capacidade Offline**: Consulta Offline (útil para `mobile` avaliar `EVIDENCIA_CONCLUSAO_EXIGIDA`
  mesmo sem conexão).

---

# Bloco 5 — Personalização

## Configuração de Personalização (White Label)

- **Objetivo**: Concentra logo, cores, tema, nome de exibição do sistema, tela de login e
  landing personalizados de um Tenant — o conteúdo de fato do que o Bloco 1 chama de "White Label"
  (ali, apenas a feature habilitada; aqui, o conteúdo).
- **Responsabilidades**: Ser consultada pelo frontend ao renderizar a experiência daquele tenant.
- **O que não faz**: Não decide se o Tenant **tem direito** a personalizar — isso é `Recurso
  Habilitado do Tenant` (Bloco 6), que verifica o Plano antes de permitir edição aqui.
- **Aggregate Root**: Sim — um registro por Tenant.
- **Bounded Context proprietário**: `settings`
- **Principais relacionamentos**: Tenant (1:1).
- **Eventos que publica**: `ConfiguracaoDePersonalizacaoAtualizada` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: só editável quando `Recurso Habilitado do Tenant` confirma a feature "White
  Label" ativa (D142 — este módulo configura, mas a permissão de uso vem de outra entidade do
  próprio módulo, não uma regra operacional externa); **nunca altera comportamento ou regra de
  negócio (D148)** — é exclusivamente visual; nenhum fluxo, permissão ou cálculo em qualquer bounded
  context pode ler um valor daqui para decidir algo.
- **Regras de negócio associadas**: D005/D006, D141, D148.
- **Estados**: Não aplicável.
- **Auditoria**: D007.
- **Linha do tempo**: alterações.
- **Anexos suportados**: logo, imagem de login (Arquivo, D024/D107 — referência a `storage`, nunca
  binário inline).
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: domínio personalizado (custom domain) para o portal do tenant.
- **Dependências obrigatórias**: Tenant.
- **Dependências proibidas**: Cliente, CT-e, Financeiro, Pneu, Viagem.
- **Dono da Timeline**: Aggregate Configuração de Personalização (este próprio).
- **Capacidade Offline**: Consulta Offline.

---

# Bloco 6 — Administração da Plataforma

## Recurso Habilitado do Tenant (Feature Flag)

- **Objetivo**: Registra, por Tenant, **apenas as exceções pontuais** de habilitação de feature (ex:
  teste beta, upgrade temporário) — nunca a fonte única de verdade sozinha.
- **Responsabilidades**: Guardar a exceção, quando existir; **nunca** ser o "quarto cadastro" que
  consolida o resultado final (D146) — o conjunto efetivo de funcionalidades de um Tenant é sempre
  calculado em tempo real cruzando Plano (Item de Plano) + esta entidade (exceção, quando houver) +
  Feature Flags globais de rollout + status da Assinatura/Licença vigente. Nenhuma tabela guarda o
  resultado já combinado.
- **O que não faz**: Não substitui o Item de Plano — só diverge dele pontualmente quando um registro
  de exceção existe; na ausência de exceção, o efetivo é puramente o que o Plano já prevê.
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `settings`
- **Principais relacionamentos**: Tenant (N:1); Item de Plano (referenciado, quando a origem é o
  Plano, não uma exceção manual).
- **Eventos que publica**: `RecursoHabilitadoParaTenant`, `RecursoDesabilitadoParaTenant` (novos).
- **Eventos que consome**: `AssinaturaRenovada`/`AssinaturaCancelada` (`subscription`) — recalcula a
  partir do Plano vigente quando não há exceção manual ativa.
- **Invariantes**: uma exceção manual tem prazo de validade opcional; ao expirar, volta a refletir o
  Plano.
- **Regras de negócio associadas**: D141, D142, D146.
- **Estados**: `Habilitado` / `Desabilitado`.
- **Auditoria**: D007.
- **Linha do tempo**: habilitação, desabilitação, expiração de exceção.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Sim, motivo da exceção manual (D023).
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: rollout gradual de feature nova (percentual de tenants).
- **Dependências obrigatórias**: Tenant.
- **Dependências proibidas**: Cliente, CT-e, Financeiro, Pneu, Viagem.
- **Dono da Timeline**: Aggregate Recurso Habilitado do Tenant (este próprio).
- **Capacidade Offline**: Consulta Offline.

## Configuração de Integração

- **Objetivo**: Representa uma integração externa habilitada para um Tenant (ex: ERP externo,
  contabilidade, e-commerce) — bounded context `integration`, distinto de `tenancy`/`settings`
  porque lida com sistemas de terceiros, não configuração interna.
- **Responsabilidades**: Guardar credenciais (referenciadas via `storage`/cofre de segredos, nunca
  em texto claro) e endpoint da integração.
- **O que não faz**: Não implementa a lógica de tradução de dados da integração — isso é
  infraestrutura (adapter), mesmo princípio já usado para `Provedor de Rastreamento`
  ([`008-rastreamento.md`](./008-rastreamento.md)).
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `integration`
- **Principais relacionamentos**: Tenant (N:1); Webhook (1:N, quando a integração é orientada a
  eventos de saída).
- **Eventos que publica**: `IntegracaoConfigurada`, `IntegracaoDesativada` (novos).
- **Eventos que consome**: Nenhum.
- **Invariantes**: credencial nunca em texto claro (mesma disciplina de `USUARIO.SENHA_HASH`,
  [`001-cadastros.md`](./001-cadastros.md)).
- **Regras de negócio associadas**: D005/D006, D107 (credencial como evidência/segredo armazenado,
  referenciado, nunca inline).
- **Estados**: `Ativa` / `Inativa` / `Com Erro`.
- **Auditoria**: D007.
- **Linha do tempo**: configuração, alterações, erros.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Sim, troubleshooting (D023).
- **KPIs relacionados**: uptime da integração (dado bruto, `analytics`).
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: marketplace de integrações prontas (ver
  [`../product/VISION.md`](../product/VISION.md)).
- **Dependências obrigatórias**: Tenant.
- **Dependências proibidas**: Cliente, CT-e, Financeiro, Pneu, Viagem diretamente.
- **Dono da Timeline**: Aggregate Configuração de Integração (este próprio).
- **Capacidade Offline**: Não.

## Webhook

- **Objetivo**: Representa um endpoint externo registrado por um Tenant para receber eventos do
  GestorFrete (ex: notificar o ERP dele quando uma Viagem é `ENCERRADA`).
- **Responsabilidades**: Guardar URL de destino, quais eventos assina, segredo de assinatura HMAC.
- **O que não faz**: Não decide o conteúdo do evento — apenas o entrega; a garantia de entrega é
  idempotente (D111/D138 — o consumidor do webhook recebe um identificador único de evento para
  deduplicar).
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `integration`
- **Principais relacionamentos**: Configuração de Integração (N:1, opcional — um webhook pode ser
  standalone, sem uma integração completa por trás).
- **Eventos que publica**: `WebhookEntregue`, `WebhookFalhou` (novos — nota: são eventos *sobre* a
  entrega, não o evento de negócio original sendo entregue).
- **Eventos que consome**: Todo evento de domínio ao qual o Tenant assinou (D032 — publicadores não
  sabem que um Webhook os consome).
- **Invariantes**: URL válida; segredo HMAC nunca em texto claro; identificador de entrega único por
  tentativa (D111).
- **Regras de negócio associadas**: D032, D111, D138 (reentrega segura), D115 (observabilidade de
  cada tentativa de entrega — início, fim, duração, tentativa, resultado, origem).
- **Estados**: `Ativo` / `Inativo` / `Suspenso` (após falhas consecutivas).
- **Auditoria**: D007.
- **Linha do tempo**: registro, entregas, falhas.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: taxa de sucesso de entrega (dado bruto, `analytics`).
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: retry com backoff exponencial configurável.
- **Dependências obrigatórias**: Tenant.
- **Dependências proibidas**: Cliente, CT-e, Financeiro, Pneu, Viagem diretamente — só consome
  eventos, nunca lê tabelas (D008).
- **Dono da Timeline**: Aggregate Webhook (este próprio).
- **Capacidade Offline**: Não.

## Execução de Job

- **Objetivo**: Registro histórico (D037) de cada execução de tarefa assíncrona em background (ex:
  geração de relatório pesado, reprocessamento de fila, job agendado de manutenção preventiva
  sugerida).
- **Responsabilidades**: Guardar tipo de job, início, fim, resultado — mesma disciplina de
  observabilidade já aplicada a integrações externas (D115), agora para jobs internos.
- **O que não faz**: Não executa o job (isso é infraestrutura/worker) — apenas registra que ele
  ocorreu e o resultado.
- **Aggregate Root**: Sim — entidade **Histórica** (D037).
- **Bounded Context proprietário**: `integration`
- **Principais relacionamentos**: Tenant (N:1, quando o job é específico de um tenant; ausente
  quando é um job de plataforma).
- **Eventos que publica**: `JobConcluido`, `JobFalhou` (novos).
- **Eventos que consome**: Nenhum — é ele quem registra a execução de outros processos.
- **Invariantes**: nunca editado após concluído (D037).
- **Regras de negócio associadas**: D037, D115.
- **Estados**: Não aplicável — é ele próprio um registro pontual.
- **Auditoria**: D007.
- **Linha do tempo**: Não aplicável (técnico, como `Evento Fiscal`/`Heartbeat`).
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: taxa de falha de job por tipo (dado bruto, `analytics`).
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: alerta automático de job crítico falhando repetidamente.
- **Dependências obrigatórias**: Nenhuma obrigatória (Tenant é opcional).
- **Dependências proibidas**: Cliente, CT-e, Financeiro, Pneu, Viagem diretamente.
- **Dono da Timeline**: Não aplicável (técnico).
- **Capacidade Offline**: Não.

---

# Bloco 7 — Notificações (D323, Sprint 10/Lote 12)

`RBAC_MATRIX.md` §7.24 já continha `notification_center.alert.view`/`.configure`/
`.channel_preference.edit` desde a preparação original da matriz — mas nenhuma entidade de Domain
jamais foi escrita para elas (mesmo padrão de D294: RBAC antecipando uma capacidade antes do
restante da cadeia a materializar). Corrigido agora, ao preparar `docs/api/086-notifications.md`
(Sprint 10, Lote 12 — Recursos Transversais), seguindo o mesmo princípio de D186 (infraestrutura
transversal, sem profile de 20 campos por entidade — mesmo tratamento dado a Anexo/Comentário).

## Notificação

- **Objetivo**: Representa uma mensagem entregue a um Usuário através de um canal (in-app, push,
  e-mail), originada por um evento de negócio de qualquer bounded context.
- **Responsabilidades**: Guardar destinatário, canal, título, mensagem, referência opcional à
  entidade relacionada, status de leitura.
- **O que não faz**: **Não é o evento de negócio** (exemplo do próprio pedido do usuário:
  `ViagemAtrasada` → Notificação → Push — o evento continua pertencendo a `freight`; Notificação é
  só o efeito colateral de entrega, nunca a origem). Não decide se deve ser enviada — isso é regra
  de aplicação consumindo o evento original (D032), nunca lógica própria desta entidade.
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `notification_center`
- **Principais relacionamentos**: Usuário (N:1, destinatário); qualquer entidade do sistema
  (referência polimórfica opcional, mesmo padrão de `anexos`/`comentarios`, D186).
- **Eventos que publica**: Nenhum — é o destino de um evento, não a origem de outro (mesmo papel de
  `Log de Auditoria`, nunca confundida com ele: Log é auditoria interna imutável, Notificação é
  comunicação ao usuário, descartável).
- **Eventos que consome**: Todo evento de domínio marcado como notificável em qualquer bounded
  context (D032 — publicadores não sabem que uma Notificação os consome).
- **Invariantes**: canal e destinatário sempre presentes; `lido_em` só preenchido quando
  `status = LIDA`.
- **Regras de negócio associadas**: D032, D320 (Notificação não é evento de domínio).
- **Estados**: `Não Lida` / `Lida`.
- **Auditoria**: Não crítica (D007 não se aplica — comunicação, não ação sensível).
- **Linha do tempo**: Não aplicável (efeito colateral, não um agregado com timeline própria).
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: taxa de leitura por canal (dado bruto, `analytics`).
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: agrupamento de notificações relacionadas (digest).
- **Dependências obrigatórias**: Usuário destinatário.
- **Dependências proibidas**: Nunca decide nem executa a regra de negócio que a originou.
- **Dono da Timeline**: Não aplicável.
- **Capacidade Offline**: Consulta Offline (mobile, D134 — receber não altera estado).

## Preferência de Canal de Notificação

- **Objetivo**: Guarda, por Usuário e por canal, se aquele canal está habilitado para receber
  notificações.
- **Responsabilidades**: Ser consultada antes de qualquer tentativa de envio por um canal
  específico.
- **O que não faz**: Não decide o conteúdo nem o evento que dispara a notificação.
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `notification_center`
- **Principais relacionamentos**: Usuário (N:1).
- **Eventos que publica**: Nenhum.
- **Eventos que consome**: Nenhum.
- **Invariantes**: no máximo um registro por Usuário/Canal.
- **Regras de negócio associadas**: D141-style (configuração pertence ao próprio usuário, nunca
  duplicada).
- **Estados**: Não aplicável — booleano `habilitado`.
- **Auditoria**: Não crítica.
- **Linha do tempo**: Não aplicável.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: granularidade por tipo de evento, não só por canal (hoje
  intencionalmente simples — `notification_center.channel_preference.edit`, singular, já reflete
  essa simplicidade no próprio nome do código RBAC).
- **Dependências obrigatórias**: Usuário.
- **Dependências proibidas**: Nenhum dado transacional.
- **Dono da Timeline**: Não aplicável.
- **Capacidade Offline**: Consulta Offline.
