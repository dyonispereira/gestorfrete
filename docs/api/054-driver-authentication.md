# 054 — Driver Authentication (Autenticação do Motorista)

Bounded context proprietário: `mobile` (D215). `sessoes_mobile` — D140: Sessão nunca representa
identidade (identidade pertence ao Motorista/Usuário), nunca cacheia RBAC (D060/D296).

## D295/D296 — Tenant e RBAC nunca vêm do dispositivo

Mesmo princípio de `001-authentication.md` (Lote 2), reforçado aqui: `tenant_id` é sempre derivado
do contexto de autenticação (D208/D295), nunca de um campo enviado pelo app. Autorização nunca é
resolvida no momento do login e cacheada na Sessão — cada ação subsequente consulta o backend ao
vivo (D060/D296), mesmo que isso signifique uma checagem por comando durante a sincronização
(`060-driver-sync.md`).

## `POST /api/v1/mobile/auth/login`

Segue exatamente o modelo de autenticação já definido no domínio — `metodo_autenticacao`
(`CPF_VEICULO`/`BIOMETRIA`/`PIN`), nunca um quarto método inventado aqui.

**Segurança**: nenhuma (pré-autenticação, mesmo padrão de `POST /auth/login`).

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          cpf: { type: string }
          vehicle_plate: { type: string, description: "Necessário quando `auth_method = CPF_VEICULO`." }
          auth_method: { type: string, enum: [CPF_VEICULO, BIOMETRIA, PIN] }
          credential: { type: string, description: "PIN ou payload biométrico, conforme `auth_method`." }
          device:
            type: object
            description: "Registra/atualiza o Dispositivo Mobile na mesma chamada (evita um segundo round-trip antes do primeiro login)."
            properties:
              device_identifier: { type: string }
              os: { type: string, enum: [ANDROID, IOS] }
              os_version: { type: string }
              app_version: { type: string }
              push_token: { type: string }
            required: [device_identifier, os, app_version]
        required: [auth_method, credential, device]
```

**Responses**

| Código | Corpo |
|---|---|
| `200` | `{ session: MobileSession, access_token, refresh_token }` |
| `400` | `BadRequest` |
| `401` | `Unauthorized` — credencial inválida |
| `403` | `Forbidden` — Motorista bloqueado (`drivers.driver.block`, `009-drivers.md`) |
| `500` | `InternalServerError` |

## `POST /api/v1/mobile/auth/refresh`

Mesmo padrão de `001-authentication.md`. **Responses**: `200` (`{ access_token, refresh_token }`),
`401`, `500`.

## `POST /api/v1/mobile/auth/logout`

Encerra a Sessão (`status = ENCERRADA`, `end_reason = LOGOUT`). **D132**: nunca revoga o
Dispositivo — `dispositivos_mobile.status` é independente.

**Responses**: `204`, `401`, `500`.

## `GET /api/v1/mobile/auth/me`

Retorna a Sessão ativa + dados essenciais do Motorista/Viagem atual — **nenhuma permissão além de
autenticado** (mesmo padrão de `GET /auth/me`, Lote 2).

**Responses**: `200` (`{ session: MobileSession, driver: Driver }` — `Driver` reaproveitado de
`components/schemas.md`, Lote 3), `401`, `500`.

## D302 — Push é só informativo

Nenhum endpoint deste documento processa payload de push recebido — receber uma notificação nunca
altera `sessoes_mobile`/`dispositivos_mobile` nem qualquer entidade de domínio. O envio de push (
`token_push`) é consumido por `notification_center` (fora do escopo deste documento); a mudança de
estado real só acontece quando o Motorista executa uma ação (login, comando de viagem, sync),
sempre validada normalmente pelo backend.

## Fora de escopo, não esquecido

- **Revogação administrativa de sessão** (`motivo_encerramento = REVOGACAO_ADMINISTRATIVA`): ação
  do Gestor/Administrador, pertence a uma futura extensão de `003-users.md`/`009-drivers.md`
  (Lote 2/3), não a este documento mobile-facing.
- **Registro/gestão de Dispositivo fora do login**: `061-driver-devices.md`.

## Como este documento cresce

Se um quinto `auth_method` for necessário (ex: token de hardware dedicado), entra pelo Domain
primeiro (D101) — o Enum físico (`sessoes_mobile_metodo_autenticacao_enum`) muda lá, este contrato
só reflete o valor novo.
