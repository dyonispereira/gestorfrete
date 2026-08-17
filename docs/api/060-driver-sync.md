# 060 — Driver Sync (Sincronização)

Bounded context proprietário: `mobile` (D215). `filas_sincronizacao`/`registros_sincronizacao` — a
tabela mais crítica do módulo (`relational/009-app_motorista.md`): idempotência, reprocessamento,
conflito, payload original e rastreabilidade, todos como colunas próprias, nunca inferidos.

## Não é um endpoint que recebe "tudo do aparelho"

`POST /mobile/sync` representa a **Fila de Sincronização já definida no domínio** (D130/D137) — um
lote de comandos atômicos, cada um com sua própria identidade (`local_id`) e posição
(`sequence`), nunca um blob genérico "estado atual do app".

## `POST /api/v1/mobile/sync`

**Segurança**: `bearerAuth` + `mobile.sync.execute` (D304).

```yaml
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          commands:
            type: array
            items: { $ref: "components/mobile-schemas.md#/SyncQueueItem" }
            minItems: 1
        required: [commands]
```

Exemplo conceitual (do kickoff, já com o nome real do comando):

```json
{
  "commands": [
    { "local_id": "a1b2c3", "sequence": 1, "command": "START_TRIP", "target_entity_type": "trip", "target_entity_id": "...", "payload": {} }
  ]
}
```

### D298 — processamento por `sequence`, nunca por ordem de chegada na rede

O backend ordena os itens do lote (e os de lotes anteriores ainda `PENDENTE`/`FALHOU` da mesma
Sessão) por `sequence` antes de processar — um `POST /mobile/sync` que chega antes de outro na rede
mas contém `sequence` maior é processado **depois**. Fisicamente garantido por
`uq_filas_sincronizacao_sessao_sequencia` (unicidade por Sessão) e pela ordenação explícita na
Application Service, nunca pela ordem de `INSERT`.

### D111/D138 — idempotência mesmo com reenvio duplicado

`local_id` (`identificador_local_unico`) é a chave de idempotência — reenviar o mesmo item (retry
automático do app após timeout, sem confirmação de recebimento) nunca cria um segundo resultado;
o backend responde com o resultado já registrado (`INSERT ... ON CONFLICT DO NOTHING` ou
equivalente, `relational/009-app_motorista.md`). D138 complementa: a própria lógica de execução do
comando é seguravelmente reexecutável — reprocessar `START_TRIP` sobre uma viagem já `EM_TRANSITO`
não duplica o efeito, retorna o estado atual.

**Responses**: `200` (`SyncBatchResponse`, `components/mobile-schemas.md`), `400`, `401`, `403`,
`500`.

## Resposta por item — D299/D300

Cada item do lote recebe um resultado independente (`SyncItemResult`) — um item `REJEITADO` nunca
impede o processamento dos demais.

| `result` | Significado |
|---|---|
| `PROCESSADO` | Comando aplicado com sucesso — `server_id` presente quando cria uma entidade nova |
| `REJEITADO` | Comando inválido para o estado atual — `error` presente, mesmo formato de `Error` (`ERROR_MODEL.md`) |
| `CONFLITO` | Comando conflita com o estado atual — `conflict.current_state`/`conflict.reason` presentes (D300 — o app nunca decide, só recebe a decisão) |
| `PENDENTE` | Comando aceito na fila, aguardando processamento assíncrono (lotes muito grandes podem não processar tudo síncrono) |

**Exemplo de conflito** (do kickoff): Motorista tenta `commands/finish` de uma Viagem já
`CANCELADA` no servidor (cancelada pelo Gestor enquanto o Motorista estava offline) →
`result: CONFLITO`, `conflict.current_state` reflete `status = CANCELADA`, `conflict.reason`
explica a divergência. **D299**: o `payload` original do comando `FINISH_TRIP` nunca é apagado —
fica preservado na linha de `filas_sincronizacao` para auditoria/revisão humana, mesmo depois do
conflito resolvido.

## `GET /api/v1/mobile/sync/records`

Histórico de lotes de sincronização já processados (`registros_sincronizacao`, D135) — leitura
pura.

**Segurança**: `mobile.sync.execute` (mesma permissão — consultar o próprio histórico de
sincronização é parte da mesma responsabilidade de sincronizar).

**Responses**: `200` (`Pagination` de `SyncRecord`), `401`, `403`, `500`.

## Permitido offline / Não permitido offline

Pedido explícito no kickoff de cruzar com `docs/domain/OFFLINE_STRATEGY.md` — **o arquivo existe
mas está vazio** (confirmado, D305). A tabela abaixo foi fundamentada diretamente em
`flows/010-APP_MOTORISTA.md` (fluxo principal, D130, D133) e no RBAC (coluna App, ●), não num
documento inexistente.

| Permitido offline (enfileirado via `060`) | Fundamento |
|---|---|
| Comandos de Viagem (`accept`/`start`/`interromper`/`retomar`/`finish`) | `flows/010-APP_MOTORISTA.md`, "Modo offline" |
| Ocorrências (`057`) | Idem + `freight.occurrence.create` ● |
| Fotos/evidências (`arquivo_id` referenciado nos comandos acima) | "Fotos capturadas em pontos obrigatórios... armazenadas localmente até upload" |
| Assinaturas (via comando de Entrega, `058`/`059`) | "Assinatura — coleta da assinatura digital... no momento da entrega" |
| Dados necessários da própria viagem (leitura, já baixados no login) | "Download da viagem... dados baixados para uso offline" |
| Checklist | **Não aplicável ainda** — sem endpoint (`056`, D305); quando existir, entra nesta lista por já ter RBAC `●` |

| Não permitido offline (nunca enfileirado) | Fundamento |
|---|---|
| Configurações administrativas (Filial, Tenant, Papéis) | Fora do Perfil Motorista (RBAC §13) |
| Financeiro (`032`–`038`) | D133-adjacente — nenhuma permissão financeira é ● |
| Fiscal (`039`–`045`) | D133 — "o app nunca possui regras fiscais" |
| RBAC (`004`/`005`) | D296 — nunca alterado pelo Mobile |
| Alteração cadastral crítica (dados do próprio Motorista além do que `009-drivers.md` já expõe como `_own`) | RBAC §13 — Motorista não tem `drivers.driver.edit` |

## Fora de escopo, não esquecido

- **Reprocessamento automático server-side de itens `FALHOU`**: mecanismo de retry em background
  não é um endpoint público — decisão de implementação, não de contrato.
- **Limite de tamanho de lote**: não fixado numericamente aqui (mesmo espírito de
  `RATE_LIMITING.md`, sem números fixados na fundação).

## Como este documento cresce

Novo `tipo_comando`/`command` (D120, vocabulário extensível) não exige mudança de schema — só um
novo valor aceito, desde que a Application Service correspondente já exista no domínio (D297,
nunca um comando novo inventado só para caber na fila).
