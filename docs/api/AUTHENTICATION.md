# AUTHENTICATION.md — Autenticação e Contexto de Tenant

## Pipeline (D208/D212 — nunca contornado)

```
Autenticação
     ↓
Tenant (derivado do contexto autenticado, nunca do body/query)
     ↓
RBAC (RBAC_MATRIX.md, mesma matriz sempre)
     ↓
Ação
```

## D208 — Tenant vem do contexto autenticado

**Nunca confiar em `tenant_id` enviado pelo cliente para selecionar dados.** Mesmo que um payload de
requisição inclua um campo `tenant_id` por algum motivo (não deveria, mas se incluir), ele é
ignorado — o `tenant_id` usado em toda consulta (`WHERE tenant_id = ...`, D005/D174) vem
exclusivamente do claim resolvido durante a autenticação (`tenant_id` no JWT, ou resolvido a partir
do API Key/Client Credential). Um usuário autenticado do Tenant A não pode, sob nenhuma
circunstância, fazer o backend ler/escrever dado do Tenant B só porque manipulou um campo do
payload — essa é a defesa de API que espelha, na camada HTTP, o que `TENANCY_MODEL.md` já garante
na camada de banco.

## Mecanismos por superfície

| Superfície | Mecanismo | Observação |
|---|---|---|
| **Web** (ERP, Frontend Next.js) | Sessão baseada em **JWT** (access token de curta duração) + refresh token em cookie `httpOnly`/`Secure`/`SameSite=Strict` | Cookie evita exposição do refresh token a `XSS`; access token curto limita janela de um token vazado |
| **Mobile** (App Motorista) | **Access Token + Refresh Token**, ambos JWT, entregues no corpo da resposta de login (app gerencia o armazenamento seguro — keychain/keystore nativo, não decidido aqui, é responsabilidade do app) | Suporta uso offline-first (D039) — o token de acesso precisa ter vida útil compatível com o padrão de sincronização de `filas_sincronizacao` (janela exata não fixada aqui, é parâmetro de implementação) |
| **API** (Pública/Interna) | **API Key** (`tokens_api`, já modelada no Modelo Relacional — `token_hash`, nunca o token em claro no banco) para integrações simples; **Client Credentials** (OAuth2, `client_id`/`client_secret` → token JWT de curta duração) quando a integração precisar de escopo mais granular que uma chave estática | `tokens_api.usuario_tecnico_id` (D174/D193) amarra toda chamada de API Key a um Usuário técnico real, nunca uma identidade anônima — RBAC se aplica a esse Usuário normalmente |
| **Webhook** (saída, GestorFrete → tenant) | Não é autenticação de entrada — é assinatura HMAC do payload enviado (`WEBHOOKS.md`), permitindo ao receptor validar a origem | Direção inversa de todas as demais linhas desta tabela |

Todo mecanismo acima usa **JWT** como formato de token (`python-jose`, já no `pyproject.toml` do
Backend) — a diferença entre "Web"/"Mobile"/"API" está em como o token é obtido e onde é
armazenado, não no formato do token em si.

## Fatores de autenticação (D-alinhado a `fatores_autenticacao`)

`fatores_autenticacao` (Modelo Relacional, `010-administracao.md`) já modela TOTP/SMS/Email/
Biometria como catálogo extensível (D120-style) por Usuário — a API expõe isso como uma etapa
opcional adicional no fluxo de login (segundo fator), nunca substituindo a senha/token principal.
Detalhe de fluxo (quando o segundo fator é obrigatório vs. opcional) é decisão de produto/segurança,
não fixada aqui.

## RBAC — D212

Toda rota autenticada consulta exatamente a mesma matriz de
[`RBAC_MATRIX.md`](../product/RBAC_MATRIX.md) — nenhuma tabela de permissão paralela, nenhum atalho
"admin bypassa tudo" fora do que a matriz já define para o papel de Administrador. O Escopo (D053 —
Empresa inteira/Filial/Unidade/Centro de Custo/Frota/Próprio usuário) é resolvido na mesma camada,
antes do Controller decidir o que retornar — um usuário com escopo "Próprio usuário" nunca recebe,
nem filtrado depois, dado de outro usuário; a query já nasce restrita.

## Sessão (`sessoes_acesso`) e Bloqueio (`bloqueios_acesso`)

Já modelados fisicamente — a API não inventa um conceito novo de sessão:

- Login bem-sucedido cria uma linha em `sessoes_acesso` (`Ativa`) — logout ou expiração por
  inatividade a move para `Encerrada`/`Expirada` (`configuracoes_numeracao`/`Parâmetro do Tenant`
  controla a política de inatividade, `010-administracao.md`).
- Revogação administrativa de sessão (`MOTIVO_ENCERRAMENTO = RevogacaoAdministrativa`) nunca
  bloqueia o Usuário (D132) — são conceitos independentes: revogar uma sessão específica vs.
  bloquear a conta inteira (`bloqueios_acesso`).

## O que a API nunca faz

- Nunca aceita `tenant_id` em query/body como fonte de verdade (D208).
- Nunca retorna o hash de senha/token em nenhuma resposta, mesmo para o próprio Usuário.
- Nunca autentica com `tenant_id` + credencial sem also resolver um Usuário real por trás — toda
  ação é sempre atribuível a um ator (D007, auditoria).

## Como este documento cresce

Estável como fundação. Detalhe fino de fluxo de login/MFA/refresh (telas exatas, tempo de expiração
de token) é responsabilidade do Backend na implementação — este documento fixa o modelo, não os
parâmetros exatos de segurança operacional.
