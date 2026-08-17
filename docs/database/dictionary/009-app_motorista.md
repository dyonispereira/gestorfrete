# 009 — App (Motorista)

Atributos distintivos das 5 entidades de
[`../../domain/009-app_motorista.md`](../../domain/009-app_motorista.md) (ver aquele arquivo para a
reconciliação D076 e o princípio "app é cliente do domínio"). Atributos universais (D069), Padrões
de atributo/Atributos Críticos (D077/D081) e a regra de indicadores nunca operacionais (D090) não
são repetidos aqui — ver [`README.md`](./README.md).

Este arquivo aplica diretamente: **D130** (offline só gera comando, nunca altera entidade),
**D131** (conflito é sempre resolvido pelo backend, nunca pelo app), **D132** (sessão expira
independente do dispositivo), **D133** (nenhum atributo fiscal aqui), **D134** (push é só
informativo), **D135** (sincronização é observável), **D136** (ordem de execução é sempre a ordem
de criação, nunca reordenada), **D137** (um item = um comando atômico), **D138** (todo comando é
reexecutável sem efeito colateral, complementa D111) e **D140** (Sessão nunca representa
identidade — apenas quem autenticou, onde e quando).

---

## Sessão Mobile

Dono: `mobile` · Natureza: Transactional Data · Aggregate Root.

Tratamento separado por pedido explícito: **Autenticação**, **Autorização**, **Expiração** e
**Revogação** são quatro preocupações distintas desta entidade, nunca misturadas em um único
conceito de "status". Por D140, nenhuma das quatro seções abaixo duplica identidade — só
`MOTORISTA_ID` referencia quem é a pessoa; tudo o mais é sobre a sessão em si (onde, quando, como).

### Autenticação

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| SESSAO_MOBILE.MOTORISTA_ID | Motorista | Referência | Sim | Capturado (sistema, no login) | Não | Interno | FK — [`001-cadastros.md`](./001-cadastros.md) |
| SESSAO_MOBILE.VEICULO_TRACIONADOR_ID | Veículo usado na autenticação | Referência | Sim | Informado (selecionado/lido no login) | Não | Interno | FK — exige `Ativo` (D003) |
| SESSAO_MOBILE.DISPOSITIVO_MOBILE_ID | Dispositivo | Referência | Sim | Capturado (sistema) | Não | Interno | FK |
| SESSAO_MOBILE.METODO_AUTENTICACAO | Método de autenticação | Enum | Sim | Capturado (sistema) | Não | Interno | Valores hoje: `CPF_Veiculo`; vocabulário extensível (mesmo princípio de D120) para Biometria/PIN futuros, sem alteração estrutural |
| SESSAO_MOBILE.TOKEN_ACESSO_HASH | Token de acesso (hash) | Texto Curto | Sim | Capturado (sistema, gerado no login) | Não | Confidencial, Crítico | Nunca em texto claro em nenhuma camada — mesma nota de segurança de `USUARIO.SENHA_HASH` ([`001-cadastros.md`](./001-cadastros.md)) |

### Autorização

Sessão Mobile **não guarda permissões** — apenas identifica quem está logado. Toda autorização é
resolvida em tempo real pelo backend consultando RBAC ([`../product/RBAC_MATRIX.md`](../product/RBAC_MATRIX.md)),
a cada requisição, nunca a partir de um campo cacheado na sessão (D060 — autorização sempre no
backend). Por isso não há atributo de "permissões" nesta entidade — seria uma cópia desatualizável
de uma fonte que já existe em `identity_access`.

### Expiração

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| SESSAO_MOBILE.DATA_HORA_INICIO | Início da sessão | Data/Hora | Sim | Capturado (sistema) | Não | Interno | Granularidade: segundo (D074) |
| SESSAO_MOBILE.DATA_HORA_EXPIRACAO_PREVISTA | Expiração prevista | Data/Hora | Sim | Calculado (início + política de inatividade do tenant) | Não | Interno | Granularidade: segundo (D074) |
| SESSAO_MOBILE.STATUS | Status | Enum | Sim | Calculado | Sim | Interno | Valores: `Ativa`/`Expirada`/`Encerrada`. Expiração é automática, por tempo — nunca uma ação humana |

### Revogação

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| SESSAO_MOBILE.DATA_HORA_ENCERRAMENTO | Encerramento | Data/Hora | Não | Capturado (sistema) | Não | Interno | Granularidade: segundo (D074) |
| SESSAO_MOBILE.MOTIVO_ENCERRAMENTO | Motivo do encerramento | Enum | Não, obrigatório quando `STATUS = Encerrada` | Informado/Capturado | Não | Interno | Valores: `Logout`/`RevogacaoAdministrativa`/`TrocaDeDispositivo`. Revogação administrativa é sempre um ato humano auditado (D010), distinto da expiração automática por tempo |
| SESSAO_MOBILE.REVOGADO_POR | Ator da revogação | Referência | Não, obrigatório quando `MOTIVO_ENCERRAMENTO = RevogacaoAdministrativa` | Capturado (sistema) | Não | Interno | D132 — revogar a sessão nunca revoga o Dispositivo Mobile; são independentes |

---

## Dispositivo Mobile

Dono: `mobile` · Natureza: Master Data · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| DISPOSITIVO_MOBILE.MOTORISTA_ID | Motorista | Referência | Sim | Capturado (sistema) | Não | Interno | FK — um motorista pode ter mais de um dispositivo ao longo do tempo |
| DISPOSITIVO_MOBILE.IDENTIFICADOR_DISPOSITIVO | Identificador do aparelho | Texto Curto | Sim | Capturado (sistema, no primeiro registro) | Não | Interno | Único globalmente (D084 — nunca reaproveitado, mesmo após troca de aparelho) |
| DISPOSITIVO_MOBILE.SISTEMA_OPERACIONAL | Sistema operacional | Enum | Sim | Capturado (sistema) | Não | Interno | Valores: `Android`/`iOS` |
| DISPOSITIVO_MOBILE.VERSAO_SO | Versão do SO | Texto Curto | Não | Capturado (sistema) | Sim, quando atualizado | Interno | |
| DISPOSITIVO_MOBILE.VERSAO_APP | Versão do app instalado | Texto Curto | Sim | Capturado (sistema) | Sim, quando atualizado | Interno | Base para o indicador de "percentual de motoristas em versão desatualizada" (calculado em `analytics`, D090) |
| DISPOSITIVO_MOBILE.TOKEN_PUSH | Token de push notification | Texto Curto | Não | Capturado (sistema) | Sim, quando renovado pelo provedor de push | Confidencial | D134 — usado apenas para envio; recebê-lo nunca altera estado de nada |
| DISPOSITIVO_MOBILE.STATUS | Status | Enum | Sim | Informado/Calculado | Sim | Interno | Valores: `Ativo`/`Inativo`/`Revogado` |
| DISPOSITIVO_MOBILE.DATA_HORA_ULTIMO_ACESSO | Último acesso | Data/Hora | Não | Derivado (D081 — projeção da última Sessão Mobile aberta neste dispositivo) | Não — projeção | Interno | Granularidade: segundo (D074); fonte de verdade é o histórico de Sessão Mobile, não este campo |

---

## Fila de Sincronização

Dono: `mobile` · Natureza: Transactional Data · Histórica (D037) · Aggregate Root.

### Atributos

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| FILA_SINCRONIZACAO.SESSAO_MOBILE_ID | Sessão de origem | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| FILA_SINCRONIZACAO.SEQUENCIA_LOCAL | Sequência local | Inteiro | Sim | Capturado (app, contador local do dispositivo) | Não | Interno | D136 — define a ordem de execução obrigatória; o backend nunca reordena, mesmo recebendo os comandos fora de ordem pela rede |
| FILA_SINCRONIZACAO.TIPO_COMANDO | Tipo de comando | Enum | Sim | Capturado (app) | Não | Interno | Vocabulário extensível (D120-style): `IniciarDeslocamento`/`ConfirmarColeta`/`ConcluirEntrega`/`RegistrarOcorrencia`/`RegistrarCanhoto`/`LeituraHodometro`/`PosicaoVeiculo`/... — D137, cada linha é sempre um único comando atômico, nunca um lote agrupado |
| FILA_SINCRONIZACAO.ENTIDADE_DESTINO_TIPO / ID | Entidade afetada | Referência (polimórfica) | Sim | Capturado (app) | Não | Interno | Aponta para a Viagem/Entrega/Ocorrência/Canhoto/etc. que o comando afeta — nunca copia o estado dela |
| FILA_SINCRONIZACAO.PAYLOAD | Dados do comando | JSON Estruturado | Sim | Capturado (app) | Não | Interno | Conteúdo específico do `TIPO_COMANDO`; anexos (fotos/assinaturas) são referências a `storage` (D107), nunca binário aqui |
| FILA_SINCRONIZACAO.IDENTIFICADOR_LOCAL_UNICO | Identificador local (chave de idempotência) | Texto Curto | Sim | Capturado (app, gerado no dispositivo) | Não | Interno | **D111 — chave de idempotência declarada**: o backend nunca processa duas vezes o mesmo `IDENTIFICADOR_LOCAL_UNICO`, mesmo com reenvio |
| FILA_SINCRONIZACAO.NUMERO_TENTATIVA | Número da tentativa | Inteiro | Sim | Capturado (sistema) | Não | Interno | Incrementado a cada reenvio |
| FILA_SINCRONIZACAO.STATUS | Status | Enum | Sim | Calculado | Sim | Interno | Valores: `Pendente`/`Enviando`/`Processada`/`Falhou`/`Conflito` |
| FILA_SINCRONIZACAO.RESOLUCAO_CONFLITO | Resolução do conflito | Texto Longo | Não, obrigatório quando `STATUS = Conflito` | Informado/Capturado (backend, ao resolver) | Não | Interno | D131 — sempre uma decisão do backend, nunca do app. **D139 — o comando original (`PAYLOAD`) nunca é apagado/sobrescrito**: esta resolução é gravada como um campo adicional do mesmo registro, preservando ambos (o que foi pedido e o que foi decidido) |

### Governança — origem, tentativa, conflito e resolução (tratamento especial pedido)

| Atributo | Origem | Tentativa | Conflito | Resolução |
|---|---|---|---|---|
| `ENTIDADE_DESTINO_TIPO/ID` | Sempre explícita (D099) — qual tela do app gerou o comando e para qual entidade | Não se aplica diretamente | Ocorre quando duas Filas de dispositivos diferentes miram a mesma entidade no mesmo período | — |
| `IDENTIFICADOR_LOCAL_UNICO` | Gerado no dispositivo, no momento da ação offline (D124/D125 — carrega `DATA_HORA_CAPTURA` implícita no comando) | Usado para descartar reprocessamento do mesmo comando reenviado (D111) | Não gera conflito por si — garante que reenvio não duplica | — |
| `NUMERO_TENTATIVA` | — | Incrementado a cada reenvio até `Processada` ou esgotar o limite de tentativas | Tentativas repetidas sem sucesso podem indicar conflito não resolvido | Escalado para `Conflito` após N tentativas falhas consecutivas |
| `STATUS = Conflito` | — | — | Detectado pelo backend ao processar (ex: Entrega já concluída por outro caminho, tentativa de duplicar Canhoto) | **Sempre resolvido pelo backend (D131)**, nunca pelo app — o app apenas exibe o resultado final ao motorista |
| `RESOLUCAO_CONFLITO` | — | — | Texto livre + o que de fato ocorreu (ex: "comando descartado, entidade já estava no estado desejado por outra via") | Registrado uma única vez, imutável após escrito (D037) |

---

## Registro de Sincronização

Dono: `mobile` · Natureza: Transactional Data · Histórica (D037) · Parte do agregado Fila de
Sincronização.

Por D135, este é o registro **do lote de sincronização** (uma sessão de sincronização pode cobrir
vários comandos da Fila de uma vez), não de um comando isolado — aquele já tem seu próprio `STATUS`
na Fila.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| REGISTRO_SINCRONIZACAO.SESSAO_MOBILE_ID | Sessão | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| REGISTRO_SINCRONIZACAO.DATA_HORA_INICIO | Início da sincronização | Data/Hora | Sim | Capturado (sistema) | Não | Interno | D135. Granularidade: segundo (D074) |
| REGISTRO_SINCRONIZACAO.DATA_HORA_FIM | Fim da sincronização | Data/Hora | Sim | Capturado (sistema) | Não | Interno | D135 |
| REGISTRO_SINCRONIZACAO.DURACAO_MS | Duração | Inteiro | Não | Calculado (`DATA_HORA_FIM − DATA_HORA_INICIO`) | Não | Interno | D135. Milissegundos |
| REGISTRO_SINCRONIZACAO.QUANTIDADE_COMANDOS | Quantidade de comandos no lote | Inteiro | Sim | Calculado | Não | Interno | D135 |
| REGISTRO_SINCRONIZACAO.QUANTIDADE_SUCESSO | Quantidade processada com sucesso | Inteiro | Sim | Calculado | Não | Interno | D135 |
| REGISTRO_SINCRONIZACAO.QUANTIDADE_FALHA | Quantidade com falha/conflito | Inteiro | Sim | Calculado | Não | Interno | D135 |

---

## Assinatura Digital

Dono: `mobile` · Natureza: Transactional Data · Aggregate Root.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| ASSINATURA_DIGITAL.DOCUMENTO_TIPO | Tipo de documento assinado | Enum | Sim | Capturado (app) | Não | Interno | Valores hoje: `Canhoto`; extensível a `Checklist`/outros no futuro sem alteração estrutural |
| ASSINATURA_DIGITAL.DOCUMENTO_ID | Documento assinado | Referência (polimórfica) | Sim | Capturado (app) | Não | Interno | Resolvido junto com `DOCUMENTO_TIPO` |
| ASSINATURA_DIGITAL.PAPEL_SIGNATARIO | Papel de quem assinou | Enum | Sim | Informado | Não | Interno | Valores: `Motorista`/`Cliente`/`Recebedor` |
| ASSINATURA_DIGITAL.NOME_SIGNATARIO_INFORMADO | Nome informado | Texto Curto | Não, obrigatório quando `PAPEL_SIGNATARIO = Recebedor` sem cadastro no sistema | Informado | Não | LGPD | Recebedor tipicamente não é um Usuário cadastrado |
| ASSINATURA_DIGITAL.ARQUIVO_ID | Imagem/traço da assinatura | Arquivo | Sim | Capturado (app) | Não | Confidencial | D107 — referência a `storage`, nunca a imagem inline |
| ASSINATURA_DIGITAL.DATA_HORA_CAPTURA | Captura | Data/Hora | Sim | Capturado (app) | Não | Interno | D124/D125. Granularidade: segundo (D074) |
| ASSINATURA_DIGITAL.DATA_HORA_RECEBIMENTO | Recebimento pelo servidor | Data/Hora | Sim | Capturado (sistema) | Não | Interno | D124/D125 |

## Como este documento cresce

Mesmo princípio de todo o dicionário: um arquivo `NNN-categoria.md` por vez, na ordem do roadmap
(ver [`README.md`](./README.md)). Próximo, por D101: `docs/domain/010-administracao.md`, antes do
dicionário correspondente.
