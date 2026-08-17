# VISION.md — GestorFrete ERP Enterprise

> Este é o documento de referência principal do produto. Toda decisão de arquitetura, produto ou
> UX que gerar dúvida deve ser resolvida consultando este documento primeiro. Quando este
> documento e uma decisão pontual entrarem em conflito, este documento prevalece até ser
> atualizado — via revisão explícita, nunca por decisão tácita dentro de uma tarefa isolada.

---

## 1. Visão Geral

GestorFrete é um ERP Enterprise, multi-tenant e nativo em nuvem, construído especificamente para
transportadoras rodoviárias de carga. Não é um ERP genérico com um módulo de "logística" anexado:
toda a modelagem de domínio (ver [`../architecture/ddd.md`](../architecture/ddd.md)) parte do
vocabulário e das regras reais de quem opera uma transportadora — do cavalo mecânico ao canhoto
assinado na entrega. O produto é desenhado para atender desde pequenas transportadoras com uma
dúzia de veículos até operações Enterprise com frotas de milhares de veículos, todas convivendo na
mesma plataforma multi-tenant.

## 2. Objetivos

- Ser o sistema em que uma transportadora gerencia sua operação **inteira**, do frete à folha de
  pagamento do motorista, sem depender de planilhas paralelas.
- Reduzir o tempo entre "eu preciso saber algo sobre minha operação" e "eu sei" — pesquisa rápida,
  filtros e relatórios exportáveis em toda tela (ver
  [`PRODUCT_PRINCIPLES.md`](./PRODUCT_PRINCIPLES.md)).
- Ser operável majoritariamente pelo celular por quem está na rua (motorista, conferente) e por
  desktop por quem está na gestão — sem forçar as duas audiências para a mesma interface.
- Crescer de dezenas para milhares de transportadoras tenant sem exigir reescrita de arquitetura —
  a multi-tenancy e os bounded contexts já existem para isso desde a fundação.

## 3. Missão

Dar a transportadoras de qualquer porte o mesmo nível de controle operacional, financeiro e de
compliance que hoje só grandes frotas com equipes de TI próprias conseguem montar sob medida —
entregando isso como um produto configurável, não como um projeto de integração customizado.

## 4. Visão

Ser a plataforma de gestão padrão do setor de transporte rodoviário de carga no Brasil, e o ponto
de entrada natural do ecossistema AgriHub (ver capítulo 19) para qualquer transportadora que também
opere no agronegócio — de modo que "abrir o GestorFrete" seja, para o gestor de uma transportadora,
o equivalente do que abrir uma planilha de Excel é hoje: o primeiro lugar que ele olha ao começar o
dia.

## 5. Valores

- **Simplicidade é uma feature.** Documentado e cobrado ativamente em
  [`PRODUCT_PRINCIPLES.md`](./PRODUCT_PRINCIPLES.md) — não é um slogan, é critério de aceite.
- **O dado do tenant é do tenant.** Isolamento multi-tenant é tratado como invariante de segurança,
  não como detalhe de implementação (ver
  [`../architecture/multi-tenancy.md`](../architecture/multi-tenancy.md)).
- **Consistência terminológica é inegociável.** O mesmo conceito tem o mesmo nome em todo lugar —
  código, tela, documentação (ver [`GLOSSARY.md`](./GLOSSARY.md)).
- **Nada crítico sem confirmação, nada excluído sem rastro.** Soft delete e auditoria são padrão,
  não exceção.
- **Arquitetura é um ativo de longo prazo.** Mudanças estruturais passam por revisão explícita —
  não são feitas "de passagem" dentro de uma tarefa que pediu outra coisa.

## 6. Filosofia do Produto

Este capítulo é o DNA do GestorFrete — o critério que resolve qualquer dúvida de produto que os
demais capítulos não cubram explicitamente.

**O GestorFrete nunca será um ERP complicado.** Toda funcionalidade deve *parecer* simples ao
usuário, mesmo quando sua implementação interna é complexa — a complexidade é um problema nosso
para resolver, nunca do usuário para enfrentar. O teste prático desse princípio é: uma pessoa deve
conseguir trabalhar o dia inteiro no sistema sem precisar de treinamento formal.

**O sistema sugere ações, não apenas mostra informação.** Um ERP tradicional informa; o GestorFrete
orienta. A diferença é concreta:

> Em vez de "Revisão vencida.", o sistema diz: "O veículo ABC-1234 está 1.250 km acima da revisão
> preventiva. Deseja abrir automaticamente uma Ordem de Serviço?"

A primeira frase exige que o usuário interprete o dado e decida o que fazer. A segunda já fez a
interpretação e propõe a próxima ação — o usuário só precisa confirmar (consistente com o princípio
de nenhuma operação crítica sem confirmação, ver [`PRODUCT_PRINCIPLES.md`](./PRODUCT_PRINCIPLES.md)).
Toda tela nova deve ser desenhada perguntando "o que o sistema pode sugerir aqui, e não apenas
mostrar?" antes de ser considerada pronta.

**O sistema é proativo, nunca reativo.** Ele antecipa o que o usuário vai precisar fazer a seguir,
em vez de esperar passivamente que o usuário descubra sozinho que algo precisa de atenção.

**O sistema reduz trabalho humano — jamais aumenta.** Qualquer funcionalidade nova é avaliada por
essa pergunta antes de qualquer outra: ela está automatizando uma decisão/ação que hoje exige
esforço manual, ou está apenas adicionando mais uma tela para o usuário preencher? Na dúvida, a
resposta errada nunca é aceitável só porque é mais simples de implementar.

**A Inteligência Artificial está presente em todos os módulos, sem parecer um chatbot.** IA no
GestorFrete não é uma caixa de chat isolada em um canto da tela — é a camada que torna o sistema
proativo, embutida no fluxo natural de cada módulo (ver capítulo 24, Inteligência Artificial). O
usuário não deve sentir que está "conversando com uma IA"; deve sentir que o sistema, como um todo,
é inteligente.

Esses princípios não são aspiracionais: são critério de aceite para qualquer tela ou fluxo
implementado a partir de agora, com o mesmo peso do que já está registrado em
[`PRODUCT_PRINCIPLES.md`](./PRODUCT_PRINCIPLES.md).

## 7. Problemas que o GestorFrete resolve

- **Fragmentação operacional**: hoje, uma transportadora média opera com planilhas para frota,
  papel para canhoto, WhatsApp para comunicação com motorista e um sistema fiscal isolado para
  CT-e/MDF-e — nenhum desses fala com o outro.
- **Falta de visibilidade financeira em tempo real**: adiantamentos, haveres e centros de custo são
  frequentemente reconciliados manualmente no fim do mês, escondendo problemas de margem até que
  seja tarde para agir.
- **Compliance manual e sujeito a erro**: CIOT, MDF-e e CT-e emitidos e conferidos manualmente
  geram risco fiscal e trabalhista evitável.
- **Manutenção reativa**: sem ciclo de pneu e histórico de manutenção centralizados, a frota é
  mantida por reação a quebra, não por prevenção — o item mais caro de se resolver tarde.
- **Sistemas legados engessados**: os TMS/ERPs de transporte estabelecidos no mercado são, em geral,
  on-premise ou SaaS de primeira geração, difíceis de estender e caros de operar em escala.

## 8. Público-alvo

Transportadoras rodoviárias de carga no Brasil, de qualquer porte, com ênfase inicial em pequenas e
médias transportadoras (o segmento mais mal atendido por sistemas Enterprise tradicionais, que
tendem a precificar e desenhar apenas para grandes frotas) e expansão para operações Enterprise
conforme a plataforma amadurece.

## 9. Personas

Detalhado em documento dedicado: [`PERSONAS.md`](./PERSONAS.md). Resumo das 15 personas
mapeadas: Diretor da Transportadora, Gestor Operacional, Analista de Frota, Mecânico, Almoxarife,
Financeiro, Faturista, Comercial, Motorista, Cliente (Embarcador) e Auditor — estas 11 atuando
dentro da transportadora — mais Consultor Comercial, Implantação, Suporte e Administrador SaaS,
papéis da equipe do próprio GestorFrete, não da transportadora.

## 10. Segmentos de Clientes

- **Pequena transportadora** (até ~20 veículos): dono opera próximo do operacional, prioriza custo
  baixo e simplicidade acima de qualquer funcionalidade avançada.
- **Média transportadora** (~20 a 200 veículos): já tem gestor operacional e financeiro dedicados,
  precisa de relatórios e controle de frota/manutenção mais robustos.
- **Grande transportadora / Enterprise** (200+ veículos): múltiplas filiais, centros de custo
  complexos, exigências de SLA, integrações próprias — cliente do "Modelo Enterprise" (capítulo 13).
- **Transportadora do agronegócio**: segmento transversal aos três portes acima, com necessidade
  específica de integração com o ecossistema AgriHub (grãos, insumos, e eventualmente
  transporte de animais vivos — ver capítulo 19).

## 11. Modelo de Negócio

SaaS multi-tenant por assinatura recorrente, precificado por combinação de porte de frota e módulos
contratados — não por desenvolvimento sob encomenda. A receita recorrente (ver bounded contexts
`subscription`, `billing`, `pricing`) é o modelo primário; o suporte a operações Enterprise é uma
camada comercial adicional sobre a mesma base de produto, não um produto/código à parte (ver
capítulo 13).

## 12. Modelo SaaS

Autoatendimento como padrão: uma nova transportadora deve conseguir se cadastrar, configurar sua
conta e começar a operar sem depender de um vendedor ou de um técnico do GestorFrete — o bounded
context `onboarding` existe justamente para isso. Planos são segmentados por porte de frota e
módulos habilitados; upgrade/downgrade de plano é self-service (`subscription`). Suporte para este
segmento é primariamente assíncrono e assistido por produto (documentação, central de ajuda,
`support`), reservando atendimento humano dedicado para os planos superiores.

## 13. Modelo Enterprise

Para transportadoras de grande porte, a mesma base multi-tenant é usada — **não** há um fork de
código ou uma instância dedicada por cliente Enterprise, isso quebraria a premissa de
escalabilidade da fundação (ver
[`../architecture/multi-tenancy.md`](../architecture/multi-tenancy.md)). O que muda é a camada
comercial: onboarding assistido pela equipe de Implantação, SLA de suporte dedicado, e
eventualmente configurações de tenant mais avançadas (múltiplas filiais/centros de custo,
integrações próprias via `integration`). Qualquer necessidade Enterprise que pareça exigir mudança
de arquitetura (não apenas de configuração/plano) deve ser tratada como uma decisão de arquitetura
sujeita a revisão, não resolvida ad-hoc.

## 14. Estratégia Comercial

- **Self-service** para pequenas/médias transportadoras: aquisição via produto (`landing`,
  `onboarding`), sem fricção de vendas.
- **Vendas diretas** para contas Enterprise e para o segmento do agronegócio, onde o ciclo de
  decisão é mais longo e passa por relacionamento.
- **Canais/parcerias**: contadores que atendem transportadoras e cooperativas/associações do
  agronegócio são canais de indicação naturais, especialmente dado o ecossistema AgriHub.

## 15. Posicionamento

"O ERP feito para transportadoras, não um ERP genérico adaptado para logística." O GestorFrete
compete pela especificidade do domínio (linguagem, fluxos e compliance do transporte rodoviário de
carga brasileiro) e pela arquitetura SaaS nativa em nuvem, contra alternativas que são genéricas
demais (ERPs corporativos adaptados) ou tecnologicamente datadas demais (TMS legados on-premise).

## 16. Concorrentes

O cenário competitivo tem três categorias, não apenas uma:

- **TMS/ERPs de transporte estabelecidos** (ex: SSW Sistemas e soluções similares), tipicamente
  mais antigos, com forte presença de mercado mas arquitetura e experiência menos modernas.
- **ERPs corporativos genéricos com módulo de logística** (ex: TOTVS Protheus, SAP Business One),
  fortes em finanças/contabilidade genéricas, fracos na linguagem específica do transporte.
- **O "não-sistema"**: planilhas, papel e WhatsApp — o concorrente real da maioria das pequenas
  transportadoras hoje, e o mais importante de vencer pela via da simplicidade, não da
  funcionalidade.

## 17. Diferenciais

- Arquitetura multi-tenant SaaS nativa em nuvem desde o primeiro dia, não uma migração tardia de um
  produto on-premise.
- Modelagem de domínio (DDD) fiel ao vocabulário real do setor (ver
  [`GLOSSARY.md`](./GLOSSARY.md)), em vez de termos genéricos de ERP.
- Mobile-first para quem está na operação (motorista, conferente), Desktop-first para quem gerencia
  — os dois desenhados para seu contexto de uso real, não uma única UI comprimida para ambos.
- Integração nativa com o ecossistema AgriHub, capturando um caso de uso que nenhum concorrente
  genérico atende de forma integrada: a transportadora que também está inserida no agronegócio.
- IA e Marketplace como capacidades de plataforma, não add-ons de terceiros.

## 18. Roadmap de 5 anos

Fases largas — sem compromissos de data específicos, a serem refinados em
[`ROADMAP.md`](./ROADMAP.md) conforme o produto avança:

- **Ano 1 — Fundação e core operacional**: arquitetura multi-tenant, `tenancy`, `identity_access`,
  `fleet`, `drivers`, `freight`, `documents`, `maintenance`, `financial` funcionais.
- **Ano 2 — Comercialização e mobilidade**: `subscription`/`billing`/`pricing`/`onboarding`
  maduros, aplicativo mobile do motorista em produção, `routing`/`tracking` em tempo real.
- **Ano 3 — Inteligência e relacionamento**: `crm`, `analytics`, `reporting` maduros, primeiros
  recursos de `ai` (precificação e previsão), `notification_center` e `support` completos.
- **Ano 4 — Rede e expansão**: `marketplace` conectando transportadoras e embarcadores, API Pública
  estável, primeira integração real com GestorPec.
- **Ano 5 — Ecossistema**: integração com GestorContábil, plataforma madura operando em escala
  (milhares de tenants), portais (Cliente, Motorista, Gestor) plenamente consolidados.

## 19. Ecossistema AgriHub

AgriHub é o ecossistema de produtos para o agronegócio do qual o GestorFrete faz parte, ao lado do
GestorPec (gestão pecuária) e, futuramente, do GestorContábil (contabilidade). A tese do
ecossistema é que uma mesma propriedade/grupo econômico do agronegócio frequentemente opera
simultaneamente produção (pecuária/agrícola), transporte próprio ou terceirizado, e contabilidade —
hoje resolvidos por sistemas isolados que não conversam. O GestorFrete é o módulo de transporte
desse ecossistema maior; sua arquitetura multi-tenant e orientada a eventos (ver
[`../architecture/event-driven.md`](../architecture/event-driven.md)) é o que permite, no futuro,
que esses produtos troquem informação sem se acoplarem estruturalmente uns aos outros.

## 20. Integração com GestorPec

Quando uma transportadora integrada ao GestorFrete realiza transporte de animais vivos para uma
operação também gerenciada no GestorPec, a visão é que dados relevantes ao transporte (guias de
trânsito animal, identificação de lote/marca de fogo, origem/destino da propriedade) fluam entre os
dois produtos sem redigitação manual. Esta integração ainda não tem contrato técnico definido — o
desenho concreto (API pública vs. eventos entre produtos) será tratado como uma decisão de
arquitetura própria, quando o GestorPec estiver maduro o suficiente para especificá-la em conjunto.

## 21. Integração futura com GestorContábil

Objetivo de longo prazo: eventos financeiros gerados no GestorFrete (faturamento de frete,
adiantamentos, haveres de motorista, centros de custo) alimentarem automaticamente os lançamentos
contábeis do GestorContábil, eliminando o retrabalho hoje feito manualmente entre a transportadora e
seu escritório de contabilidade. Assim como a integração com GestorPec, o contrato técnico exato
será definido quando ambos os produtos estiverem em estágio compatível — nesta etapa, a única
decisão tomada é que o `financial`/`billing` do GestorFrete deve permanecer a fonte de verdade dos
eventos financeiros da operação de transporte, publicados de forma que um consumidor externo (como
o GestorContábil) possa futuramente assiná-los.

## 22. Marketplace

O bounded context `marketplace` existe para, no futuro, conectar transportadoras (capacidade
ociosa de frota) a embarcadores (carga a transportar) dentro da própria plataforma — um efeito de
rede que nenhum ERP fechado consegue oferecer. É explicitamente uma capacidade de fase posterior
(ver roadmap, Ano 4): depende de uma base relevante de transportadoras já operando no GestorFrete
antes de fazer sentido economicamente.

## 23. API Pública

Visão de longo prazo para permitir que transportadoras Enterprise e parceiros de integração
(GestorPec, GestorContábil, sistemas de clientes/embarcadores) consumam dados do GestorFrete de
forma programática e suportada, versionada e documentada — formalizando o que hoje é apenas a API
interna (`apps/api`) usada pelo próprio frontend. O contrato público (autenticação, versionamento,
rate limiting, escopo de dados expostos) será detalhado em [`../api/`](../api/) quando a API interna
estiver madura o suficiente para ser exposta com segurança e estabilidade a terceiros.

## 24. Inteligência Artificial

Este capítulo concretiza, tecnicamente, a Filosofia do Produto (capítulo 6) no que se refere a
IA. O bounded context `ai` é reservado para capacidades que aumentam a decisão do gestor e do
motorista, não para automação que remove controle do usuário: precificação dinâmica de frete
sugerida (nunca aplicada sem confirmação — consistente com o princípio de nenhuma operação crítica
sem confirmação), previsão de prazo de entrega, sugestão de manutenção preventiva a partir do ciclo
de pneu e histórico de uso, e otimização de rotas/alocação de frota. Nenhum recurso de IA está
implementado nesta etapa — o bounded context existe como estrutura reservada.

## 25. Aplicativo Mobile

Consumidor primário do bounded context `mobile` e da persona Motorista: aplicativo mobile-first
para o motorista executar coleta/entrega, registrar canhoto, reportar problemas de manutenção e
consultar adiantamentos/haveres — desenhado para uso com conectividade instável (ver
[`PRODUCT_PRINCIPLES.md`](./PRODUCT_PRINCIPLES.md), Mobile First). É a superfície de produto mais
crítica para adoção pelo motorista, persona com menor tolerância a fricção de uso.

## 26. Portal do Cliente

Superfície voltada à persona Cliente (Embarcador): acompanhamento de status de coleta/entrega,
acesso a documentos fiscais (CT-e/MDF-e) e canhotos das suas cargas, sem acesso a nenhum outro dado
operacional da transportadora. É a base sobre a qual o `marketplace` (capítulo 22) poderá ser
construído no futuro.

## 27. Portal do Motorista

Sobreposição de conceito com o Aplicativo Mobile (capítulo 25) mas não idêntico: o "portal" é a
superfície de consulta (adiantamentos, haveres, histórico de viagens, documentos pessoais), que
pode existir tanto dentro do app mobile quanto como acesso web leve — a decisão de unificar os dois
em uma única superfície ou mantê-los distintos é uma decisão de produto ainda em aberto, a ser
tratada quando o desenho do app mobile avançar.

## 28. Portal do Gestor

A experiência desktop-first consumida pelas personas Diretor, Gestor Operacional, Analista de
Frota, Financeiro, Faturista e Comercial — no fundo, o próprio `apps/web` na sua configuração
principal. "Portal do Gestor" nomeia essa experiência como conceito de produto para distingui-la
explicitamente do Portal do Cliente e do app do Motorista, que têm necessidades de UX muito
diferentes (ver capítulo 2, Mobile First vs. Desktop First).

## 29. Landing Page

Superfície pública de marketing/aquisição (bounded context `landing`), fora da área autenticada,
responsável pela conversão de visitante em conta criada via `onboarding`. Não é a página inicial do
produto autenticado — é a porta de entrada para quem ainda não é cliente.

## 30. Objetivos Técnicos

- Disponibilidade compatível com uso Enterprise (meta de SLA a ser formalizada quando houver
  operação em produção — ver [`NFR.md`](./NFR.md)).
- API First e versionada como padrão de integração entre frontend, mobile e futura API pública.
- Escalar para milhares de tenants sobre a mesma infraestrutura, conforme desenhado em
  [`../architecture/multi-tenancy.md`](../architecture/multi-tenancy.md), sem exigir reescrita de
  arquitetura para crescer.
- Conformidade contínua com LGPD e com as obrigações fiscais/regulatórias do setor (SEFAZ, ANTT,
  CONTRAN) como requisito técnico permanente, não um projeto pontual.

## 31. Objetivos Financeiros

Nesta etapa, o objetivo financeiro é expresso como **prioridade de modelo**, não como meta numérica
(metas específicas de ARR/NRR/CAC:LTV dependem de unit economics ainda não validados e serão
definidas em revisão dedicada, não fabricadas aqui): priorizar receita recorrente previsível
(assinatura) sobre receita de projeto único, e priorizar retenção/expansão de contas existentes
(upsell de módulos e planos) sobre aquisição pura — coerente com o Modelo SaaS (capítulo 12).

## 32. Indicadores do Produto

Categorias de indicador que o produto deve estar instrumentado para medir (os alvos numéricos serão
definidos por módulo conforme cada um for implementado, não nesta etapa de fundação):

- **Ativação**: tempo entre criação da conta e primeiro frete despachado com sucesso.
- **Engajamento**: frequência de uso por persona (ex: DAU/WAU do app do motorista).
- **Adoção por módulo**: quais bounded contexts contratados estão realmente em uso.
- **Satisfação**: NPS segmentado por persona (o Motorista e o Diretor tendem a ter percepções muito
  diferentes do mesmo produto).
- **Saúde operacional da plataforma**: erros, latência e disponibilidade por tenant.

## 33. Restrições

- Regulatórias: emissão/validação de CT-e e MDF-e depende de integração com SEFAZ; operações com
  motorista autônomo dependem de CIOT junto à ANTT; composições veiculares (bitrem, rodotrem) são
  regidas por limites do CONTRAN — o produto deve refletir essas regras, não contorná-las.
- Legais: LGPD aplica-se a dados de motoristas, usuários e, potencialmente, clientes/embarcadores.
- Operacionais: conectividade instável no campo é a norma, não a exceção — qualquer superfície
  usada por motorista deve tolerar isso (ver capítulo 25).
- Arquiteturais: a arquitetura está congelada por decisão explícita — nenhuma mudança estrutural
  (novos bounded contexts, renomeações, novos padrões de pasta) sem revisão prévia.

## 34. Escalabilidade

Tratada em profundidade em [`../architecture/multi-tenancy.md`](../architecture/multi-tenancy.md):
isolamento lógico por `tenant_id` (não schema/database por tenant), preparado para particionamento
futuro caso a escala exija. A escalabilidade é uma propriedade da arquitetura, não uma otimização a
ser adicionada quando o produto "ficar grande" — por isso já está na fundação, antes de qualquer
linha de código de negócio.

## 35. Estratégia Cloud

Nativo em nuvem desde a fundação: aplicações containerizadas (ver
[`../adr/0003-docker-infra.md`](../adr/0003-docker-infra.md)), dependências de infraestrutura
(PostgreSQL, Redis, RabbitMQ, MinIO) tratadas como serviços gerenciáveis independentemente da
aplicação, arquitetura Event-Driven que permite escalar bounded contexts de forma desacoplada. A
escolha de provedor de nuvem e de orquestração em produção (Kubernetes ou equivalente) é uma decisão
de infraestrutura a ser tomada — e revisada — quando o produto se aproximar de operação real, não
antecipada sem necessidade nesta etapa de fundação.

## 36. Futuro do Produto

O GestorFrete começa como o ERP de uma transportadora individual, mas sua arquitetura já é a de um
nó dentro de um ecossistema maior (AgriHub). O sucesso de longo prazo do produto não é medido
apenas por quantas transportadoras o usam, mas por quão natural se torna, para uma transportadora
do agronegócio, ter GestorFrete, GestorPec e GestorContábil como uma única experiência de gestão —
mesmo sendo, tecnicamente, produtos e bounded contexts independentes que escolheram se comunicar
por contrato, não por acoplamento.
