# AUTHENTICATION_AND_DEVICE_IMPLEMENTATION.md — Sessão Mobile, Dispositivo Mobile

Fonte: `dictionary/009-app_motorista.md`, `relational/009-app_motorista.md`, `054-driver-
authentication.md`, `061-driver-devices.md`.

## `SessaoMobile` compartilha PK com `Sessão` de `identity_access` (D407)

`sessoes_mobile` não tem RBAC nem representa identidade (D140) — só quem autenticou, onde, quando.
Mas o JWT emitido precisa ser validado pelo mesmo `SessionValidator`/`get_current_actor` já usado
por toda a API (D303 aplicado à infraestrutura, não só ao domínio). Solução: `POST /mobile/auth/
login` cria **duas linhas com o mesmo `id`** — uma `Session` (`sessoes_acesso`, via
`SqlAlchemySessionRepository`, sem nenhuma mudança em `identity_access`) e uma `SessaoMobile`
(`sessoes_mobile`, campos ricos: `motorista_id`/`veiculo_tracionador_id`/`dispositivo_mobile_id`/
`metodo_autenticacao`). O JWT carrega esse `id` como `session_id`, exatamente como todo outro login
já emite. Logout/expiração/revogação encerram as duas linhas juntas — `TROCA_DE_DISPOSITIVO` (só
existe no Enum de `mobile`) mapeia para `SessionEndedReason.LOGOUT` no lado `identity_access`.

## Login por CPF+Veículo resolve tenant pelo par, nunca pelo CPF isolado (D408)

`motoristas.cpf`/`veiculos_tracionadores.placa` são únicos só por tenant — diferente de
`usuarios.email` (Lote 2). `POST /mobile/auth/login` busca **todos** os Motoristas com aquele CPF
em **todos** os tenants (`DriverRepository.list_by_cpf_across_tenants`, novo, mesma exceção
documentada de `UserRepository.get_by_email`), e para cada candidato verifica se existe um Veículo
`ATIVO` com aquela placa **no mesmo tenant** (`VehicleRepository.get_by_placa_and_tenant`, novo).
Zero ou mais de um par válido → `401` genérico (nunca revela qual parte falhou).

## `credential` aceito, nunca validado para `CPF_VEICULO` (D409)

Nenhum documento (Domain/Dictionary/DDL) especifica um segredo armazenado para este método — o
único invariante é "CPF de Motorista Apto + Veículo Ativo". `credential` satisfaz a validação
Pydantic (campo obrigatório no schema congelado) e não é comparado a nada. Quando `BIOMETRIA`/`PIN`
forem implementados de verdade, este é o ponto de extensão.

## Bloqueio do Motorista / Veículo inativo

`404`/`401` gerado ao autenticar — nunca vaza qual dos dois. `drivers.driver.block` (RBAC) é a ação
administrativa que leva `Driver.fitness_status = BLOQUEADO`; login rejeita com `403`
(`MOBILE_DRIVER_BLOCKED`) quando esse é o caso, distinto de CPF/placa não encontrados (`401`) —
distinção explícita porque a Auditoria #5 (tenant/identidade) e o próprio domínio tratam bloqueio
como um estado do Motorista, não uma credencial errada.

## `MobileDevice` — autoatendimento, D132

Criado só como parte de `POST /mobile/auth/login` (nunca um `POST` dedicado — `061`). `identificador_
dispositivo` nunca muda depois do primeiro registro; se já existe (troca de sessão no mesmo
aparelho), reaproveitado, nunca duplicado (`uq_dispositivos_mobile_identificador`). `PATCH
/mobile/devices/{id}` (`mobile.device.edit_own`) atualiza `os_version`/`app_version`/`push_token`/
`status(ATIVO/INATIVO)` — nunca dispara efeito de domínio (D134/D302, Auditoria #7). Revogar uma
`SessaoMobile` (`logout`, `motivo=REVOGACAO_ADMINISTRATIVA` futuro) nunca toca
`dispositivos_mobile.status` — tabelas independentes, sem FK/trigger cruzado (Auditoria #4).

## Erros de domínio

`MOBILE_LOGIN_INVALID_CREDENTIALS` (401), `MOBILE_DRIVER_BLOCKED` (403), `MOBILE_SESSION_NOT_FOUND`
(404), `MOBILE_DEVICE_NOT_FOUND` (404), `MOBILE_DEVICE_FORBIDDEN` (403 — dispositivo de outro
Motorista).

## Auditoria e tenant isolation

`SessaoMobile`/`MobileDevice` filtram por `get_current_tenant_id()` normalmente após o login (a
resolução do tenant em si é a única exceção documentada, D208-style, igual ao login Web). Login/
logout geram `logs_auditoria` (D007).
