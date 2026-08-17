# 009 — App (Motorista)

Entidades do bounded context `mobile` — o aplicativo do motorista. Template completo de 22 campos
(ver [`README.md`](./README.md)).

## Princípio fundamental: o app é um cliente do domínio, não um domínio paralelo

`mobile` **não tem regras de negócio próprias** sobre Viagem, Entrega, Ocorrência, Canhoto,
Checklist ou Motorista — todas essas já pertencem a `freight`, `documents`, `maintenance` e
`drivers`, com suas próprias máquinas de estado (D035) já documentadas. O app **consome e executa**
essas regras através da mesma API que qualquer outro cliente usaria; o que `mobile` de fato possui é
a experiência de campo: sessão, dispositivo, fila offline e captura de assinatura. Nenhuma entidade
abaixo redefine estado de negócio de outro bounded context — todas apenas o referenciam ou
transportam. Em particular (D133): **`mobile` nunca possui regra fiscal alguma** — não calcula
imposto, não gera CT-e/MDF-e, não valida nada fiscal; isso é exclusivo de `documents`
([`007-fiscal.md`](./007-fiscal.md)), consumido pelo app apenas como leitura.

### Fluxo da Viagem no App — mapeamento, não reinvenção

Por pedido explícito, o "fluxo completo da viagem" (aceitar, iniciar, pausas, retomada, finalizar)
é documentado aqui como **mapeamento de ações do app para transições já existentes** em
[`002-VIAGEM.md`](../flows/002-VIAGEM.md) — nenhuma delas é redefinida:

| Ação no app | Transição correspondente (já existente) | Onde vive |
|---|---|---|
| Aceitar viagem atribuída | **Não corresponde a uma transição de `STATUS_OPERACIONAL`** — a Viagem já está `PLANEJADA` a partir da Alocação de Recurso ([`002-operacao.md`](../database/dictionary/002-operacao.md)); o "aceite" no app é um reconhecimento do Motorista, não um novo estado de negócio (ver Gap identificado, abaixo) | `freight` (Viagem), reconhecido por `mobile` |
| Iniciar deslocamento | `LIBERADA → EM_DESLOCAMENTO` | `freight` |
| Chegar à origem / iniciar carregamento | `EM_DESLOCAMENTO → CARREGANDO` | `freight` |
| Confirmar carga conferida | `CARREGANDO → EM_TRANSITO` | `freight` |
| Chegar a um ponto de entrega | `EM_TRANSITO → EM_ENTREGA` | `freight` |
| Concluir entrega (com Canhoto) | `EM_ENTREGA → EM_TRANSITO` (multi-drop) ou `→ FINALIZADA` (última parada) | `freight` |
| Pausa por pane/ocorrência grave | `[qualquer estado em rota] → INTERROMPIDA` | `freight` |
| Retomada após pausa | `INTERROMPIDA → [estado anterior]` | `freight` |
| Registrar Ocorrência | Criação de `Ocorrência` (sem mudar `STATUS_OPERACIONAL` por si só) | `freight` |
| Assinar Canhoto | `Canhoto.STATUS: Pendente → Registrado` | `freight` (Canhoto é parte do agregado Viagem) |

**Gap identificado (D104) — resolvido por D129**: a máquina de estados de Viagem
([`002-VIAGEM.md`](../flows/002-VIAGEM.md)) não tinha uma transição formal para "aceite do
motorista". Decisão tomada: o aceite **é um Domain Event, nunca um novo status** (D129) —
`MotoristaAceitouViagem` é publicado pelo app, alimenta a Timeline Universal (D022) e a auditoria
(D007) normalmente, mas a Viagem permanece `PLANEJADA`; nenhum estado operacional novo foi criado.
Isso evita o erro clássico de transformar toda ação do usuário em um status da máquina de estados —
nem toda ação é uma transição.

## Reconciliação de nomes (D076)

A lista original em `ENTITY_CATALOG.md` tinha 6 entidades: Sessão Mobile, Assinatura Digital,
Registro de Sincronização, Item Pendente de Sincronização, Indicador de Desempenho do Motorista,
Configuração de Ranking Interno.

| Original | Decisão | Por quê |
|---|---|---|
| Indicador de Desempenho do Motorista | **Removida** | Viola D090 — indicador agregado/estatístico nunca é entidade do domínio operacional; é calculado por `analytics` a partir de dados que `freight`/`drivers` já possuem (pontualidade, ocorrências, avarias) |
| Configuração de Ranking Interno | **Removida** | Mesma razão — ranking é uma visão de BI/gamificação sobre indicadores, não um dado de domínio de `mobile` |
| Item Pendente de Sincronização | Renomeada **Fila de Sincronização** | Nome mais preciso — é a fila em si, cada item é uma linha dela, não uma entidade conceitualmente separada |
| Sessão Mobile, Assinatura Digital, Registro de Sincronização | Mantidas | Já corretas |
| — | **Nova**: Dispositivo Mobile | Necessária para separar o conceito de sessão (transiente, uma por login) do dispositivo físico em si (persistente, dono do push token/versão do app, usado por múltiplas sessões ao longo do tempo) |

Resultado: **5 entidades** (não as 6 originais — duas removidas por violarem D090, uma nova
identificada, líquido -1).

---

## Sessão Mobile

- **Objetivo**: Representa uma sessão autenticada do app no dispositivo de um Motorista. Por D140,
  Sessão Mobile **nunca representa identidade** — identidade pertence ao Usuário/Motorista
  ([`001-cadastros.md`](./001-cadastros.md)); a sessão só representa quem autenticou, em qual
  dispositivo e durante qual período.
- **Responsabilidades**: Autenticar via CPF + Veículo (mecanismo inicial); manter o token de acesso
  válido; registrar início/fim de sessão.
- **O que não faz**: Não decide permissões — isso é RBAC ([`../product/RBAC_MATRIX.md`](../product/RBAC_MATRIX.md)),
  consultado normalmente via `identity_access`; não substitui o Usuário — referencia um.
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `mobile`
- **Principais relacionamentos**: Usuário/Motorista (referenciado, [`001-cadastros.md`](./001-cadastros.md));
  Dispositivo Mobile (N:1); Veículo Tracionador (referenciado, usado na autenticação).
- **Eventos que publica**: `SessaoMobileIniciada`, `SessaoMobileEncerrada` (novos).
- **Eventos que consome**: Nenhum.
- **Invariantes**: autenticação exige CPF válido de Motorista `Apto` (`001-cadastros.md`,
  `STATUS_APTIDAO`) **e** um Veículo Tracionador `Ativo`; sessão expira após período configurável de
  inatividade; expiração de Sessão nunca implica revogação do Dispositivo Mobile, e vice-versa —
  são eventos independentes (D132).
- **Regras de negócio associadas**: D051–D062 (RBAC — a sessão carrega identidade, a autorização em
  si é sempre resolvida no backend, D027/D060); autenticação por CPF+Veículo é o mecanismo inicial,
  com espaço explícito para múltiplos fatores no futuro (ex: biometria, PIN) sem mudança estrutural
  — o campo de método de autenticação é um Enum extensível, mesmo princípio de D120 aplicado aqui.
- **Estados**: `Ativa` / `Expirada` / `Encerrada`.
- **Auditoria**: D007 — login/logout são eventos sensíveis.
- **Linha do tempo**: própria — início, encerramento, expiração.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: Nenhum direto (dado bruto para `analytics`, se necessário, D090).
- **Documentos canônicos relacionados**: Nenhum ainda — candidata a um fluxo próprio em
  `docs/flows/010-APP_MOTORISTA.md` (já existe, revisar quando este domain doc for consumido pela
  próxima etapa).
- **Evoluções futuras previstas**: múltiplos fatores de autenticação (D124-style extensibilidade).
- **Dependências obrigatórias**: Usuário/Motorista, Veículo Tracionador, Dispositivo Mobile.
- **Dependências proibidas**: Cliente, CT-e, Financeiro, Pneu — a sessão nunca acessa esses
  diretamente, apenas via as APIs normais de cada bounded context.
- **Dono da Timeline**: Aggregate Sessão Mobile (este próprio).
- **Capacidade Offline**: Não se aplica à autenticação inicial (exige conectividade); a sessão, uma
  vez obtida, permite uso offline das demais funcionalidades (D039).

## Dispositivo Mobile

- **Objetivo**: Representa o aparelho físico (smartphone/tablet) usado por um Motorista — persistente
  entre sessões, ao contrário de Sessão Mobile.
- **Responsabilidades**: Guardar identificador do dispositivo, sistema operacional/versão, versão do
  app instalada, token de push notification, status.
- **O que não faz**: Não autentica sozinho — é referenciado por Sessão Mobile, nunca a substitui.
  **Receber uma push notification nunca altera estado de nada (D134)** — o token aqui guardado só
  permite o envio; a mudança de estado só ocorre quando o usuário, a partir da notificação, executa
  uma ação validada normalmente pelo backend.
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `mobile`
- **Principais relacionamentos**: Usuário/Motorista (referenciado, N:1 — um motorista pode trocar de
  aparelho); Sessão Mobile (1:N).
- **Eventos que publica**: `DispositivoMobileRegistrado` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: identificador do dispositivo único globalmente (D084 — nunca reutilizado mesmo
  após troca de aparelho).
- **Regras de negócio associadas**: D005/D006, D084.
- **Estados**: `Ativo` / `Inativo` (ex: motorista desligado, dispositivo revogado).
- **Auditoria**: D007.
- **Linha do tempo**: registro, atualizações de versão do app.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: percentual de motoristas em versão desatualizada do app (dado bruto,
  `analytics`).
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: gestão de múltiplos dispositivos autorizados por motorista, com
  revogação remota.
- **Dependências obrigatórias**: Usuário/Motorista.
- **Dependências proibidas**: Cliente, CT-e, Financeiro, Pneu, Viagem diretamente.
- **Dono da Timeline**: Aggregate Dispositivo Mobile (este próprio).
- **Capacidade Offline**: Consulta Offline (o próprio registro do dispositivo é lido localmente após
  o primeiro registro).

## Fila de Sincronização

- **Objetivo**: Representa a fila local de ações realizadas offline por um Motorista, aguardando
  envio ao servidor quando a conectividade retornar.
- **Responsabilidades**: Guardar cada comando pendente (tipo, payload, tentativas), na ordem em que
  ocorreram; nunca decidir sozinha o resultado de negócio do comando — apenas transportá-lo até a
  API correta (Viagem, Entrega, Ocorrência, Canhoto, Leitura de Hodômetro, Posição de Veículo — cada
  uma já com sua própria capacidade offline documentada, D039). **Enquanto offline, nenhuma entidade
  é alterada diretamente pelo app (D130)** — o que existe localmente é o comando enfileirado; a
  execução de fato (validação de regra, mudança de estado) só ocorre quando o backend o processa.
- **O que não faz**: Não interpreta o conteúdo do comando — é transporte, não negócio; **nunca
  resolve conflito sozinha (D131)** quando dois comandos colidem (ex: duas alterações do mesmo
  recurso em dispositivos diferentes) — a resolução é sempre uma decisão do backend, registrada em
  Registro de Sincronização, seguindo a regra de negócio de cada entidade afetada (ex: D037/D018 —
  histórico nunca sobrescreve, então a maioria dos conflitos se resolve por "as duas coexistem no
  histórico", não por descarte).
- **Aggregate Root**: Sim — entidade **Histórica** por natureza (D037): um item processado nunca é
  removido, apenas marcado como concluído (D001).
- **Bounded Context proprietário**: `mobile`
- **Principais relacionamentos**: Sessão Mobile (referenciada, N:1); a entidade de destino de cada
  ação (Viagem, Entrega, Ocorrência, Canhoto, etc.) é referenciada por ID e tipo, nunca copiada.
- **Eventos que publica**: `AcaoOfflineEnfileirada`, `AcaoOfflineProcessada`,
  `AcaoOfflineFalhou` (novos).
- **Eventos que consome**: Nenhum — é ela quem inicia o envio.
- **Invariantes**: comandos são executados **exatamente** na ordem em que foram criados no
  dispositivo — nunca reordenados automaticamente, mesmo que cheguem fora de ordem pela rede (D136);
  cada item representa exatamente um comando atômico, nunca um lote de operações agrupadas (D137 —
  "iniciar viagem", "registrar foto" e "informar abastecimento" são três comandos distintos, nunca
  "executar toda a viagem" como um só); todo comando é reexecutável sem efeito colateral (D138,
  complementa D111); toda ação tem origem explícita (D099 — qual tela/funcionalidade do app a
  gerou).
- **Regras de negócio associadas**: D039 (Offline First seletivo — só existe fila para as
  funcionalidades já listadas como offline em cada entidade, nunca para Financeiro/Administração,
  reforçando a decisão original), D124/D125 (a ação carrega o momento de captura no dispositivo,
  distinto do momento de sincronização/processamento no servidor), D136, D137, D138.
- **Estados**: `Pendente` / `Enviando` / `Processada` / `Falhou` / `Conflito`.
- **Auditoria**: D007.
- **Linha do tempo**: própria — criação local, tentativas de envio, resultado.
- **Anexos suportados**: referências a Arquivo (fotos, assinaturas) já enviadas ao módulo de
  armazenamento (`storage`) antes do item entrar na fila, ou enfileiradas junto (D107 — nunca o
  binário dentro do item da fila).
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: tempo médio de sincronização, taxa de conflito (dado bruto, `analytics`).
- **Documentos canônicos relacionados**: `docs/flows/010-APP_MOTORISTA.md` (já existe — a ser
  cruzado na próxima etapa).
- **Evoluções futuras previstas**: priorização de sincronização por criticidade (ex: Canhoto antes
  de foto de paisagem).
- **Dependências obrigatórias**: Sessão Mobile.
- **Dependências proibidas**: Nenhuma restrição de bounded context de destino — por natureza,
  referencia qualquer entidade com Capacidade Offline (D039), mas nunca duplica a regra de negócio
  dela.
- **Dono da Timeline**: Aggregate Fila de Sincronização (este próprio) para o transporte; a entidade
  de destino mantém sua própria timeline de negócio, inalterada.
- **Capacidade Offline**: Sim (D039) — é, por definição, a própria infraestrutura de offline do app.

## Registro de Sincronização

- **Objetivo**: Registro histórico (D037) do resultado de cada tentativa de sincronização — sucesso,
  falha, conflito e como foi resolvido.
- **Responsabilidades**: Ser a fonte de auditoria de "o que aconteceu quando o app tentou
  sincronizar" — por D135, toda sincronização registra início, fim, quantidade de comandos
  processados, sucesso, falhas e tempo total, não apenas o resultado de um comando isolado.
- **O que não faz**: Não é editável — apenas inserido (D037/D123, mesmo princípio de leituras
  imutáveis de dispositivo externo aplicado aqui a ações de cliente mobile).
- **Aggregate Root**: Não — parte do agregado Fila de Sincronização; entidade **Histórica** (D037).
- **Bounded Context proprietário**: `mobile`
- **Principais relacionamentos**: Fila de Sincronização (N:1, cada item pode ter múltiplas
  tentativas registradas).
- **Eventos que publica**: Nenhum diretamente — refletido pelos eventos da Fila.
- **Eventos que consome**: Nenhum.
- **Invariantes**: nunca editado após inserido (D037); toda tentativa registra resultado explícito
  (D115 — observabilidade: início, fim, duração, tentativa, resultado, origem, mesmo padrão de
  `Evento Fiscal`).
- **Regras de negócio associadas**: D017/D018/D037, D111 (a idempotência de reenvio depende de um
  identificador local único por ação, gerado no dispositivo, para o servidor nunca processar a
  mesma ação duas vezes mesmo com retry), D115.
- **Estados**: Não aplicável — registro pontual.
- **Auditoria**: D007 — é, ele mesmo, um artefato de auditoria de sincronização.
- **Linha do tempo**: parte da Fila de Sincronização.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: taxa de sucesso de sincronização por versão do app/dispositivo (dado bruto,
  `analytics`).
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: alertas automáticos de motorista com alto índice de falha de
  sincronização (possível problema de conectividade regional).
- **Dependências obrigatórias**: Fila de Sincronização.
- **Dependências proibidas**: Cliente, CT-e, Financeiro, Pneu.
- **Dono da Timeline**: Aggregate Fila de Sincronização.
- **Capacidade Offline**: Não — este registro só existe no servidor, após a tentativa de
  sincronização ocorrer (o lado do dispositivo mantém seu próprio log local, fora do domínio).

## Assinatura Digital

- **Objetivo**: Representa a captura de uma assinatura eletrônica no app (Motorista, Cliente ou
  Recebedor) para um documento que exige — hoje, principalmente o Canhoto
  ([`002-operacao.md`](./002-operacao.md)); futuramente, Checklist ou outros.
- **Responsabilidades**: Guardar a imagem/traço da assinatura (referência a `storage`, D107), quem
  assinou (papel: Motorista/Cliente/Recebedor) e a que documento se aplica.
- **O que não faz**: Não decide sozinha o efeito de negócio da assinatura (ex: "Canhoto registrado")
  — isso é responsabilidade do documento assinado (`Canhoto.STATUS`, `documents`/`freight`); a
  Assinatura Digital é a evidência capturada, referenciada pelo documento, nunca o contrário.
- **Aggregate Root**: Sim — entidade que referencia seu documento de forma polimórfica (mesmo padrão
  de `Evento Fiscal`, [`007-fiscal.md`](./007-fiscal.md)).
- **Bounded Context proprietário**: `mobile`
- **Principais relacionamentos**: Documento assinado (referência polimórfica — Canhoto hoje,
  extensível a outros no futuro).
- **Eventos que publica**: `AssinaturaDigitalCapturada` (novo) — consumido pelo documento referenciado
  para decidir seu próprio efeito de negócio (D032).
- **Eventos que consome**: Nenhum.
- **Invariantes**: nunca editada após capturada (D037/D123); toda Assinatura Digital referencia
  exatamente um documento e um papel de quem assinou.
- **Regras de negócio associadas**: D107 (a imagem é evidência armazenada, nunca um campo de texto/
  blob aqui), D037/D123 (imutável).
- **Estados**: Não aplicável — registro pontual, imutável.
- **Auditoria**: D007.
- **Linha do tempo**: consumida pela Timeline do documento assinado (D022).
- **Anexos suportados**: a própria imagem/traço da assinatura (Arquivo, `storage`) (D024/D107).
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: assinatura com validade jurídica reforçada (certificado ICP-Brasil
  do assinante, quando exigido por cliente/contrato).
- **Dependências obrigatórias**: o documento que está sendo assinado (Canhoto, hoje).
- **Dependências proibidas**: Cliente/Financeiro diretamente (é lida por eles apenas via o documento
  que referencia, nunca diretamente), CT-e, Pneu.
- **Dono da Timeline**: Aggregate do documento assinado (ex: Viagem, via Canhoto).
- **Capacidade Offline**: Sim (D039) — capturada localmente, sincronizada via Fila de Sincronização.
