# 010 — Administração (Plataforma)

Atributos distintivos das 20 entidades de
[`../../domain/010-administracao.md`](../../domain/010-administracao.md) (ver aquele arquivo para a
reconciliação D076 e os princípios D141/D142). Atributos universais (D069), Padrões de atributo/
Atributos Críticos (D077/D081) e a regra de indicadores nunca operacionais (D090) não são repetidos
aqui — ver [`README.md`](./README.md).

Este arquivo aplica: **D143** (configuração crítica tem histórico), **D144** (configuração pode ter
vigência), **D145** (padrão × sobrescrita no mesmo registro, nunca duplicado), **D146** (recursos
efetivos são sempre derivados, nunca um quarto cadastro), **D147** (auditoria nunca depende do ator
existir) e **D148** (personalização nunca altera comportamento).

---

# Bloco 1 — Plataforma SaaS

## Tenant

Dono: `tenancy` · Natureza: Master Data · Aggregate Root de mais alto nível.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| TENANT.RAZAO_SOCIAL | Razão Social | Texto Curto | Sim | Informado | Sim | Interno | |
| TENANT.CNPJ | CNPJ | Texto Curto | Sim | Informado | Não | Confidencial | Único na plataforma (não por tenant — é o próprio identificador) |
| TENANT.STATUS | Status | Enum | Sim | Calculado | Sim | Interno | Valores: `Trial`/`Ativo`/`Suspenso`/`Cancelado`. Suspensão bloqueia login, nunca exclui dados (D001) |
| TENANT.DATA_CRIACAO | Data de criação | Data | Sim | Capturado (sistema) | Não | Interno | Granularidade: dia (D074) |

## Plano

Dono: `subscription` · Natureza: Platform Reference Data (D046) · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| PLANO.NOME | Nome | Texto Curto | Sim | Informado | Não | Interno | Único na plataforma |
| PLANO.PRECO_BASE | Preço base | Monetário | Sim | Informado | Sim, quando revisado | Financeiro | Moeda: BRL (D075) |
| PLANO.STATUS | Status | Enum | Sim | Informado | Não | Interno | Valores: `Ativo`/`Descontinuado` |

## Item de Plano

Dono: `subscription` · Natureza: Platform Reference Data (D046) · Parte do agregado Plano.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| ITEM_PLANO.PLANO_ID | Plano | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| ITEM_PLANO.CHAVE_FEATURE | Chave da feature/limite | Texto Curto | Sim | Informado | Não | Interno | Ex: `MAX_VEICULOS`, `WHITE_LABEL`, `MODULO_RASTREAMENTO` — vocabulário extensível (D120-style) |
| ITEM_PLANO.VALOR | Valor do limite/feature | Texto Curto | Sim | Informado | Não | Interno | Ex: `"20"` (limite numérico) ou `"true"` (feature booleana) — tipo implícito na `CHAVE_FEATURE` |

## Assinatura

Dono: `subscription` · Natureza: Transactional Data · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| ASSINATURA.TENANT_ID | Tenant | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| ASSINATURA.PLANO_ID | Plano | Referência | Sim | Informado | Sim, em upgrade/downgrade | Interno | |
| ASSINATURA.STATUS | Status | Enum | Sim | Calculado | Sim | Interno | Valores: `Trial`/`Ativa`/`Cancelada`/`Suspensa` |
| ASSINATURA.DATA_INICIO_TRIAL | Início do trial | Data | Não | Capturado (sistema) | Não | Interno | Granularidade: dia (D074) |
| ASSINATURA.DATA_FIM_TRIAL | Fim do trial | Data | Não | Calculado (início + prazo do trial) | Não | Interno | Granularidade: dia (D074) |

## Cobrança Recorrente

Dono: `billing` · Natureza: Transactional Data · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| COBRANCA_RECORRENTE.ASSINATURA_ID | Assinatura | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| COBRANCA_RECORRENTE.VALOR | Valor | Monetário | Sim | Capturado (Plano vigente no momento da cobrança) | Não | Financeiro | D097 — valor desta cobrança, moeda BRL (D075), no momento da geração |
| COBRANCA_RECORRENTE.DATA_VENCIMENTO | Vencimento | Data | Sim | Calculado | Não | Interno | Granularidade: dia (D074) |
| COBRANCA_RECORRENTE.STATUS | Status | Enum | Sim | Calculado | Sim | Interno | Valores: `Pendente`/`Paga`/`Falhou`/`Cancelada`. Imutável após `Paga` e conciliada (D100) |

---

# Bloco 2 — Identidade

## Grupo de Usuários

Dono: `identity_access` · Natureza: Master Data · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| GRUPO_USUARIOS.NOME | Nome | Texto Curto | Sim | Informado | Não | Interno | Único por tenant |
| GRUPO_USUARIOS.STATUS | Status | Enum | Sim | Informado | Não | Interno | Valores: `Ativo`/`Inativo` |

## Convite

Dono: `identity_access` · Natureza: Transactional Data · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| CONVITE.EMAIL | E-mail | Texto Curto | Sim | Informado | Não | LGPD | Único por Convite pendente no tenant |
| CONVITE.PAPEL_ID | Papel proposto | Referência | Sim | Informado | Não | Interno | FK — [`001-cadastros.md`](./001-cadastros.md) |
| CONVITE.DATA_EXPIRACAO | Expiração | Data/Hora | Sim | Calculado (envio + prazo configurável) | Não | Interno | Granularidade: segundo (D074) |
| CONVITE.STATUS | Status | Enum | Sim | Calculado | Sim | Interno | Valores: `Pendente`/`Aceito`/`Expirado`/`Revogado` |

## Fator de Autenticação

Dono: `identity_access` · Natureza: Master Data · Parte do agregado Usuário.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| FATOR_AUTENTICACAO.USUARIO_ID | Usuário | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| FATOR_AUTENTICACAO.TIPO | Tipo de fator | Enum | Sim | Informado | Não | Interno | Vocabulário extensível (D120-style): `TOTP`/`SMS`/`Email`/`Biometria` — preparação, validação plena é evolução futura |
| FATOR_AUTENTICACAO.STATUS | Status | Enum | Sim | Informado | Não | Interno | Valores: `Ativo`/`Inativo` |

---

# Bloco 3 — Segurança

## Sessão de Acesso (Web/Portal)

Dono: `identity_access` · Natureza: Transactional Data · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| SESSAO_ACESSO.USUARIO_ID | Usuário | Referência | Sim | Capturado (sistema) | Não | Interno | FK — D140, aponta identidade, mas a sessão em si não é identidade |
| SESSAO_ACESSO.DATA_HORA_INICIO | Início | Data/Hora | Sim | Capturado (sistema) | Não | Interno | Granularidade: segundo (D074) |
| SESSAO_ACESSO.DATA_HORA_EXPIRACAO_PREVISTA | Expiração prevista | Data/Hora | Sim | Calculado (política de inatividade — `Parâmetro do Tenant`, Bloco 4) | Não | Interno | Granularidade: segundo (D074) |
| SESSAO_ACESSO.MOTIVO_ENCERRAMENTO | Motivo do encerramento | Enum | Não | Informado/Capturado | Não | Interno | Valores: `Logout`/`RevogacaoAdministrativa`. Revogar nunca bloqueia o Usuário (D132) |
| SESSAO_ACESSO.STATUS | Status | Enum | Sim | Calculado | Sim | Interno | Valores: `Ativa`/`Expirada`/`Encerrada` |

## Token de API

Dono: `identity_access` · Natureza: Transactional Data · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| TOKEN_API.USUARIO_TECNICO_ID | Usuário técnico | Referência | Sim | Capturado (sistema) | Não | Interno | FK — RBAC do Usuário técnico, nunca um caminho paralelo (D061) |
| TOKEN_API.TOKEN_HASH | Token (hash) | Texto Curto | Sim | Capturado (sistema, gerado na criação) | Não | Confidencial, Crítico | Nunca em texto claro; nunca reutilizado (D084) |
| TOKEN_API.DATA_HORA_ULTIMO_USO | Último uso | Data/Hora | Não | Derivado (D081 — projeção) | Não — projeção | Interno | Granularidade: segundo (D074) |
| TOKEN_API.STATUS | Status | Enum | Sim | Calculado | Sim | Interno | Valores: `Ativo`/`Revogado`. Revogação é definitiva — novo uso exige novo token |

## Bloqueio de Acesso

Dono: `identity_access` · Natureza: Transactional Data · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| BLOQUEIO_ACESSO.USUARIO_ID | Usuário | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| BLOQUEIO_ACESSO.TIPO | Tipo | Enum | Sim | Calculado | Não | Interno | Valores: `Automático` (tentativas falhas)/`Administrativo` |
| BLOQUEIO_ACESSO.MOTIVO | Motivo | Texto Longo | Não, obrigatório quando `TIPO = Administrativo` | Informado | Não | Interno | D010 — decisão explícita |
| BLOQUEIO_ACESSO.STATUS | Status | Enum | Sim | Calculado | Sim | Interno | Valores: `Vigente`/`Removido` |

## Log de Auditoria

Dono: `audit` · Natureza: Transactional Data · Histórica (D037) · Aggregate Root.

### Atributos

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| LOG_AUDITORIA.ENTIDADE_TIPO / ENTIDADE_ID | Entidade afetada | Referência (polimórfica) | Sim | Capturado (sistema) | Não | Interno | Qualquer entidade auditável do sistema |
| LOG_AUDITORIA.ACAO | Ação | Enum | Sim | Capturado (sistema) | **É ele próprio o histórico** — nunca editado (D037) | Interno | Valores: `Criação`/`Alteração`/`Exclusão Lógica`/`Login`/`Logout`/`Transição de Status`/... (vocabulário extensível) |
| LOG_AUDITORIA.ATOR_ID | Ator | Referência | Não (nulo quando `Sistema`) | Capturado (sistema) | Não | Interno | FK — pode ser nulo para ações automáticas |
| LOG_AUDITORIA.ATOR_NOME_SNAPSHOT | Nome do ator (snapshot) | Texto Curto | Sim | Capturado, uma única vez, no momento do registro (D071/D147) | Não (D073) | Interno | D147 — nunca ressincroniza; preserva o significado mesmo se o Usuário for removido depois |
| LOG_AUDITORIA.ORIGEM | Origem | Enum | Sim | Capturado (sistema) | Não | Interno | Valores: `Web`/`Mobile`/`API`/`Sistema` |
| LOG_AUDITORIA.DADOS_ANTES | Dados antes | JSON Estruturado | Não | Capturado (sistema) | Não | Confidencial | Ausente em `Criação` |
| LOG_AUDITORIA.DADOS_DEPOIS | Dados depois | JSON Estruturado | Não | Capturado (sistema) | Não | Confidencial | Ausente em `Exclusão Lógica` |
| LOG_AUDITORIA.MOTIVO | Motivo | Texto Longo | Não, obrigatório em ações sensíveis (D010) | Informado | Não | Interno | Ex: motivo de revogação, cancelamento |
| LOG_AUDITORIA.ID_CORRELACAO | Identificador de correlação | Texto Curto | Sim | Capturado (sistema) | Não | Interno | Agrupa múltiplos Logs originados de uma mesma transação de negócio (ex: uma transição de Viagem que dispara efeitos em três bounded contexts) |
| LOG_AUDITORIA.DATA_HORA | Data/hora | Data/Hora | Sim | Capturado (sistema) | Não | Interno | Granularidade: segundo (D074) |

### Governança de Log de Auditoria (tratamento especial pedido)

| Dimensão | Atributo(s) | Observação |
|---|---|---|
| Quem | `ATOR_ID` + `ATOR_NOME_SNAPSHOT` | Referência viva + snapshot — nunca perde significado mesmo com o Usuário removido depois (D147) |
| Quando | `DATA_HORA` | Granularidade segundo (D074) |
| Origem | `ORIGEM` | De onde partiu a ação — Web/Mobile/API/Sistema |
| Antes | `DADOS_ANTES` | Estado anterior, quando aplicável |
| Depois | `DADOS_DEPOIS` | Estado resultante, quando aplicável |
| Motivo | `MOTIVO` | Obrigatório em ações sensíveis (D010), livre nas demais |
| Correlação | `ID_CORRELACAO` | Uma única ação de negócio pode gerar múltiplos Logs (ex: em `freight`, `financial` e `documents` simultaneamente) — todos compartilham o mesmo identificador |
| Rastreabilidade | `ENTIDADE_TIPO`/`ENTIDADE_ID` + imutabilidade total | Nunca editado/apagado (D001/D037/D109) — é a própria garantia de integridade do sistema |

---

# Bloco 4 — Configurações

## Configuração Regional do Tenant

Dono: `settings` · Natureza: Master Data · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| CONFIGURACAO_REGIONAL.TENANT_ID | Tenant | Referência | Sim | Capturado (sistema) | Não | Interno | FK 1:1, imutável |
| CONFIGURACAO_REGIONAL.FUSO_HORARIO | Fuso horário | Texto Curto | Sim | Informado | Sim, quando alterado | Interno | "Timezone"/"Fuso" — mesmo conceito. Ex: `America/Sao_Paulo` |
| CONFIGURACAO_REGIONAL.IDIOMA | Idioma | Enum | Sim | Informado | Sim | Interno | Ex: `pt-BR` |
| CONFIGURACAO_REGIONAL.MOEDA_PADRAO | Moeda padrão | Texto Curto | Sim | Informado | Sim | Interno | Hoje sempre BRL (D075) — campo existe para expansão futura |

## Configuração de Numeração

Dono: `settings` · Natureza: Master Data · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| CONFIGURACAO_NUMERACAO.TENANT_ID | Tenant | Referência | Sim | Capturado (sistema) | Não | Interno | FK |
| CONFIGURACAO_NUMERACAO.TIPO_ENTIDADE | Tipo de entidade numerada | Enum | Sim | Informado | Não | Interno | Ex: `Viagem`/`OrdemServico` — nunca documento fiscal (D110, exclusivo de `Configuração Fiscal do Tenant`, [`007-fiscal.md`](./007-fiscal.md)) |
| CONFIGURACAO_NUMERACAO.PREFIXO | Prefixo | Texto Curto | Não | Informado | Sim | Interno | |
| CONFIGURACAO_NUMERACAO.PROXIMO_NUMERO | Próximo número | Inteiro | Sim | Calculado (incrementado a cada uso) | Não — é o próprio contador | Interno | Nunca decresce nem é reutilizado (D084) |

## Parâmetro do Tenant

Dono: `settings` · Natureza: Transactional Data · Histórica (D037/D143) · Aggregate Root.

Tratamento especial pedido — sete conceitos, cada um seu próprio atributo, nunca colapsados:

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| PARAMETRO_TENANT.CHAVE | Chave | Texto Curto | Sim | Capturado (catálogo de chaves do sistema) | Não | Interno | Vocabulário extensível (D120-style): `ALCADA_APROVACAO_MANUTENCAO`, `EVIDENCIA_CONCLUSAO_EXIGIDA`, futuros |
| PARAMETRO_TENANT.TIPO_VALOR | Tipo | Enum | Sim | Capturado (junto à chave) | Não | Interno | Valores: `Monetário`/`Booleano`/`Inteiro`/`Decimal`/`Texto` — declarado para o consumidor nunca adivinhar (D097-style) |
| PARAMETRO_TENANT.CATEGORIA | Categoria | Enum | Sim | Capturado (junto à chave) | Não | Interno | Ex: `Aprovação`/`Aplicativo`/`Operacional` — agrupa chaves para navegação na tela de configuração |
| PARAMETRO_TENANT.VALOR_PADRAO_PLATAFORMA | Valor padrão da plataforma | Texto Curto | Sim | Capturado (catálogo de chaves do sistema) | Não | Interno | D145 — o valor herdado, igual para todo tenant que não sobrescreve; nunca editável pelo tenant |
| PARAMETRO_TENANT.VALOR_SOBRESCRITO_TENANT | Valor sobrescrito pelo Tenant | Texto Curto | Não | Informado | Sim (D143 — nova sobrescrita gera novo registro, nunca edita o anterior) | Interno | D145 — quando presente, prevalece sobre o padrão; quando ausente, o efetivo é o padrão |
| PARAMETRO_TENANT.TENANT_ID | Tenant | Referência | Sim | Capturado (sistema) | Não | Interno | FK |
| PARAMETRO_TENANT.DATA_INICIO_VIGENCIA | Início da vigência | Data/Hora | Sim | Capturado (sistema) | Não | Interno | D144. Granularidade: segundo (D074) |
| PARAMETRO_TENANT.DATA_FIM_VIGENCIA | Fim da vigência | Data/Hora | Não | Capturado (sistema, ao ser substituído) | Não | Interno | D144 — ex: nova alçada já agendada para valer a partir de uma data futura |
| PARAMETRO_TENANT.STATUS | Status | Enum | Sim | Calculado | Sim | Interno | Valores: `Vigente`/`Substituído` — no máximo um `Vigente` por `CHAVE`/Tenant em cada instante |

---

# Bloco 5 — Personalização

## Configuração de Personalização (White Label)

Dono: `settings` · Natureza: Master Data · Aggregate Root.

Tratamento especial pedido — tudo referenciando `storage`, nunca binário inline (D107):

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| CONFIGURACAO_PERSONALIZACAO.TENANT_ID | Tenant | Referência | Sim | Capturado (sistema) | Não | Interno | FK 1:1 |
| CONFIGURACAO_PERSONALIZACAO.LOGO_ARQUIVO_ID | Logo | Imagem | Não | Informado | Sim, quando trocado | Interno | D107 — referência a `storage` |
| CONFIGURACAO_PERSONALIZACAO.FAVICON_ARQUIVO_ID | Favicon | Imagem | Não | Informado | Sim | Interno | D107 |
| CONFIGURACAO_PERSONALIZACAO.COR_PRIMARIA | Cor primária | Texto Curto | Não | Informado | Sim | Interno | Código hexadecimal |
| CONFIGURACAO_PERSONALIZACAO.COR_SECUNDARIA | Cor secundária | Texto Curto | Não | Informado | Sim | Interno | Código hexadecimal |
| CONFIGURACAO_PERSONALIZACAO.FONTE | Fonte tipográfica | Texto Curto | Não | Informado | Sim | Interno | Nome da fonte (Google Fonts ou equivalente) — não um arquivo, referência de nome |
| CONFIGURACAO_PERSONALIZACAO.IMAGEM_LOGIN_ARQUIVO_ID | Imagem da tela de login | Imagem | Não | Informado | Sim | Interno | D107 |
| CONFIGURACAO_PERSONALIZACAO.NOME_SISTEMA_EXIBICAO | Nome do sistema exibido | Texto Curto | Não | Informado | Sim | Interno | Ex: substituir "GestorFrete" pela marca do tenant, quando White Label habilitado |
| CONFIGURACAO_PERSONALIZACAO.CONFIGURACAO_LANDING_ARQUIVO_ID | Landing page personalizada | Arquivo | Não | Informado | Sim | Interno | D107 — referência a um bundle armazenado (HTML/config), nunca inline |
| CONFIGURACAO_PERSONALIZACAO.TEMPLATE_EMAIL_ARQUIVO_ID | Template de e-mail | Arquivo | Não | Informado | Sim | Interno | D107 — referência ao template usado nos e-mails transacionais do tenant |
| CONFIGURACAO_PERSONALIZACAO.STATUS | Status | Enum | Sim | Calculado | Não | Interno | Valores: `Ativa`/`Inativa`. **D148 — nenhum destes campos jamais é lido por uma regra de negócio**, apenas pela camada de apresentação |

---

# Bloco 6 — Administração da Plataforma

## Recurso Habilitado do Tenant (Feature Flag)

Dono: `settings` · Natureza: Transactional Data · Aggregate Root — **camada de exceção, nunca a
consolidação final (D146)**.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| RECURSO_HABILITADO.TENANT_ID | Tenant | Referência | Sim | Capturado (sistema) | Não | Interno | FK |
| RECURSO_HABILITADO.CHAVE_FEATURE | Chave da feature | Texto Curto | Sim | Informado | Não | Interno | Mesmo vocabulário de `ITEM_PLANO.CHAVE_FEATURE` |
| RECURSO_HABILITADO.TIPO_EXCECAO | Tipo de exceção | Enum | Sim | Informado | Não | Interno | Valores: `HabilitaAlemDoPlano`/`DesabilitaApesarDoPlano` |
| RECURSO_HABILITADO.DATA_FIM_VALIDADE | Validade da exceção | Data | Não | Informado | Não | Interno | Granularidade: dia (D074); ao expirar, o efetivo volta a refletir só o Plano |

## Configuração de Integração

Dono: `integration` · Natureza: Master Data · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| CONFIGURACAO_INTEGRACAO.TENANT_ID | Tenant | Referência | Sim | Capturado (sistema) | Não | Interno | FK |
| CONFIGURACAO_INTEGRACAO.TIPO | Tipo de integração | Enum | Sim | Informado | Não | Interno | Ex: `ERP Externo`/`Contabilidade` |
| CONFIGURACAO_INTEGRACAO.CREDENCIAL_ARQUIVO_ID | Credencial | Arquivo | Sim | Informado | Não | Confidencial, Crítico | D107 — referência a cofre de segredos, nunca texto claro |
| CONFIGURACAO_INTEGRACAO.STATUS | Status | Enum | Sim | Calculado | Sim | Interno | Valores: `Ativa`/`Inativa`/`Com Erro` |

## Webhook

Dono: `integration` · Natureza: Master Data · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| WEBHOOK.TENANT_ID | Tenant | Referência | Sim | Capturado (sistema) | Não | Interno | FK |
| WEBHOOK.URL_DESTINO | URL de destino | Texto Curto | Sim | Informado | Sim, quando alterada | Interno | |
| WEBHOOK.EVENTOS_ASSINADOS | Eventos assinados | JSON Estruturado | Sim | Informado | Sim | Interno | Lista de tipos de evento de domínio |
| WEBHOOK.SEGREDO_HMAC_ARQUIVO_ID | Segredo HMAC | Arquivo | Sim | Capturado (sistema) | Não | Confidencial, Crítico | D107 — nunca texto claro |
| WEBHOOK.STATUS | Status | Enum | Sim | Calculado | Sim | Interno | Valores: `Ativo`/`Inativo`/`Suspenso` (após falhas consecutivas) |

## Execução de Job

Dono: `integration` · Natureza: Transactional Data · Histórica (D037) · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| EXECUCAO_JOB.TENANT_ID | Tenant | Referência | Não | Capturado (sistema) | Não | Interno | Ausente quando o job é de plataforma, não de um tenant específico |
| EXECUCAO_JOB.TIPO_JOB | Tipo de job | Enum | Sim | Capturado (sistema) | Não | Interno | Vocabulário extensível (D120-style) |
| EXECUCAO_JOB.DATA_HORA_INICIO | Início | Data/Hora | Sim | Capturado (sistema) | Não | Interno | D115. Granularidade: segundo (D074) |
| EXECUCAO_JOB.DATA_HORA_FIM | Fim | Data/Hora | Não | Capturado (sistema) | Não | Interno | D115 |
| EXECUCAO_JOB.RESULTADO | Resultado | Enum | Não | Capturado (sistema) | Não | Interno | Valores: `Sucesso`/`Falha`. D115 |

---

# Bloco 7 — Notificações (D323, adicionado no Sprint 10/Lote 12)

## Notificação

Dono: `notification_center` · Natureza: Transactional Data · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| NOTIFICACAO.USUARIO_DESTINATARIO_ID | Destinatário | Referência | Sim | Capturado (sistema) | Não | Interno | FK |
| NOTIFICACAO.CANAL | Canal | Enum | Sim | Capturado (sistema) | Não | Interno | Valores: `InApp`/`Push`/`Email` |
| NOTIFICACAO.EVENTO_ORIGEM_TIPO | Evento de origem | Texto Curto | Sim | Capturado (sistema) | Não | Interno | Nome do evento de domínio que originou (ex.: `ViagemAtrasada`) — nunca o próprio evento, D320 |
| NOTIFICACAO.ENTIDADE_TIPO / ENTIDADE_ID | Entidade relacionada | Referência (polimórfica) | Não | Capturado (sistema) | Não | Interno | Mesmo padrão de `anexos`/`comentarios` (D186) |
| NOTIFICACAO.TITULO | Título | Texto Curto | Sim | Capturado (sistema) | Não | Interno | |
| NOTIFICACAO.MENSAGEM | Mensagem | Texto Longo | Sim | Capturado (sistema) | Não | Interno | |
| NOTIFICACAO.STATUS | Status | Enum | Sim | Calculado | Sim | Interno | Valores: `NaoLida`/`Lida` |
| NOTIFICACAO.DATA_HORA_ENVIO | Enviada em | Data/Hora | Sim | Capturado (sistema) | Não | Interno | Granularidade: segundo (D074) |
| NOTIFICACAO.DATA_HORA_LEITURA | Lida em | Data/Hora | Não | Capturado (sistema) | Não | Interno | Preenchido só quando `STATUS = Lida` |

## Preferência de Canal de Notificação

Dono: `notification_center` · Natureza: Master Data · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| PREFERENCIA_NOTIFICACAO.USUARIO_ID | Usuário | Referência | Sim | Capturado (sistema) | Não | Interno | FK |
| PREFERENCIA_NOTIFICACAO.CANAL | Canal | Enum | Sim | Informado | Não | Interno | Valores: `InApp`/`Push`/`Email` |
| PREFERENCIA_NOTIFICACAO.HABILITADO | Habilitado | Booleano | Sim | Informado | Não | Interno | Único por Usuário/Canal |

## Como este documento cresce

Mesmo princípio de todo o dicionário: um arquivo `NNN-categoria.md` por vez, na ordem do roadmap
(ver [`README.md`](./README.md)). Próximo, por D101: `docs/domain/011-bi.md`, antes do dicionário
correspondente. Bloco 7 (Notificações) foi adicionado retroativamente no Sprint 10/Lote 12 (D323),
mesma disciplina de auditoria aplicada a toda API deste sprint.
