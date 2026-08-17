# VERSIONING.md — Versionamento da API

## D207 — API versionada por path

Todas as APIs públicas e do produto começam em `/api/v1`. A versão pertence ao **contrato**, não a
um parâmetro de execução:

```
/api/v1/viagens
/api/v1/ordens-servico
```

**Nunca aceito como mecanismo principal**:

```
/api/viagens?version=2          -- versão como query string
Accept: application/vnd.gestorfrete.v2+json   -- versionamento por header/content-negotiation
```

Motivo: versão no path é visível, cacheável, roteável no API Gateway sem inspecionar o corpo/header
da requisição, e não pode ser "esquecida" silenciosamente pelo cliente (uma query string opcional
tende a virar `v1` por omissão, mesmo quando o cliente já deveria estar em `v2`).

## O que força uma nova versão (`v2`)

Mudança **incompatível** — quebra um cliente que já integra com `v1` sem alteração nenhuma do lado
dele:

- Remover um campo do payload de resposta
- Remover ou renomear um endpoint
- Tornar obrigatório um campo de requisição que antes era opcional
- Mudar o tipo/formato de um campo existente (ex.: `valor` de `string` para `number`)
- Mudar o significado de um `error.code` já existente (D209 já proíbe isso mesmo dentro da mesma
  versão)

## O que NÃO força nova versão (mudança compatível, cabe dentro de `v1`)

- Adicionar um novo endpoint
- Adicionar um campo novo e opcional no payload de resposta
- Adicionar um novo valor a um enum já documentado como extensível (D120-style)
- Adicionar um novo filtro/parâmetro de query opcional (`FILTERING_SORTING.md`)
- Depreciar um campo/endpoint (marcar como `deprecated` no OpenAPI) sem removê-lo ainda

## Ciclo de vida de uma versão

```
v1 lançada
     │
     ▼
v2 lançada (quando uma mudança incompatível é genuinamente necessária)
     │
     ▼
v1 marcada deprecated — janela de convivência anunciada explicitamente aos consumidores
(duração exata não fixada agora — depende de quem consome v1 no momento, decisão de produto)
     │
     ▼
v1 desativada — só depois que todo consumidor conhecido migrou, nunca por prazo automático
```

Convivência de múltiplas versões é sempre **por path completo** (`/api/v1/...` e `/api/v2/...`
respondendo simultaneamente) — nunca uma versão "escondida" atrás de feature flag no mesmo path.

## Versionamento dentro do módulo IA (nota de coerência com D166/D169)

`inferencias_ia.modelo_ia_versao` (Modelo Relacional) já versiona o *modelo de IA* usado — isso é
ortogonal ao versionamento de API: um endpoint `/api/v1/sugestoes-ia` pode continuar em `v1`
enquanto o modelo de IA por trás evolui de versão livremente; o contrato HTTP não muda só porque o
modelo mudou.

## Como este documento cresce

Estável. Toda decisão de criar `v2` (quando acontecer) é registrada em
[`../product/DECISIONS.md`](../product/DECISIONS.md) com a lista exata de mudanças incompatíveis
que a motivaram — nunca uma bump de versão "por precaução".
