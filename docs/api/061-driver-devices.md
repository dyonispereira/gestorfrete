# 061 — Driver Devices (Dispositivos Mobile)

Bounded context proprietário: `mobile` (D215). `dispositivos_mobile` — D132: revogar sessão nunca
bloqueia o Dispositivo (tabelas independentes, sem `ON DELETE`/trigger cruzado).

## Escopo: autoatendimento, nunca gestão administrativa

Este documento cobre só o Dispositivo do próprio Motorista da sessão — RBAC `mobile.device.
view_own`/`.edit_own` (D304). Revogação administrativa de dispositivo (Gestor forçando logout de
um aparelho perdido/roubado) não tem código RBAC hoje — fora de escopo deste lote, ver "Fora de
escopo" abaixo.

## `GET /api/v1/mobile/devices`

Lista os dispositivos já registrados para o Motorista da sessão (normalmente 1, pode haver
histórico de troca de aparelho).

**Segurança**: `bearerAuth` + `mobile.device.view_own`.

**Responses**: `200` (`Pagination` de `MobileDevice`, `components/mobile-schemas.md`), `401`,
`403`, `500`.

## `GET /api/v1/mobile/devices/{id}`

**Segurança**: `mobile.device.view_own` — `403` se o dispositivo não pertence ao Motorista da
sessão.

**Responses**: `200` (`MobileDevice`), `401`, `403`, `500`.

## `PATCH /api/v1/mobile/devices/{id}`

D229 — parcial. Campos que o próprio dispositivo atualiza a cada abertura do app (`os_version`/
`app_version`/`push_token`) ou quando o Motorista opta por desvincular o aparelho
(`status = INATIVO`, autoatendimento — distinto de `REVOGADO`, que é administrativo).

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          os_version: { type: string }
          app_version: { type: string }
          push_token: { type: string }
          status: { type: string, enum: [ATIVO, INATIVO] }
```

**Segurança**: `mobile.device.edit_own`.

**Responses**: `200` (`MobileDevice`), `400`, `401`, `403`, `404`, `500`.

## `identificador_dispositivo` nunca muda

Não incluído no corpo do `PATCH` — é a identidade física do aparelho (`uq_dispositivos_mobile_
identificador`), definida uma única vez no primeiro login (`054-driver-authentication.md`). Trocar
de aparelho sempre cria um novo `MobileDevice`, nunca reescreve o identificador de um existente.

## Sem `POST`/`DELETE`

- **`POST`**: o Dispositivo é criado como parte de `POST /mobile/auth/login` (`054`) — nunca um
  endpoint separado, evita um dispositivo "órfão" sem sessão associada.
- **`DELETE`**: `RBAC_MATRIX.md` não tem `mobile.device.delete` — desativação via `PATCH
  status=INATIVO`, mesmo padrão de toda entidade com campo de status neste sistema.

## Fora de escopo, não esquecido

- **Revogação administrativa** (`status = REVOGADO`, Gestor forçando logout remoto de um aparelho):
  RBAC não tem código para essa ação a partir do ERP Web — não inventado aqui; candidato natural a
  uma extensão futura de `009-drivers.md` (Lote 3) quando o produto definir esse fluxo.
- **Histórico de trocas de dispositivo**: não modelado como entidade própria — `MobileDevice.
  status = INATIVO` em registros antigos já preserva o histórico implicitamente (D001, nunca
  excluído fisicamente).

## Como este documento cresce

Se revogação administrativa for pedida no futuro, o RBAC ganha o código primeiro (mesmo processo
de D271/D283/D293/D304), só depois o endpoint correspondente (provavelmente em `009-drivers.md`,
não aqui — este documento é a visão do próprio Motorista, não a do Gestor).
