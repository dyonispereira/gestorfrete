# RATE_LIMITING.md — Limitação de Taxa

Nenhum número definitivo fixado nesta sprint — os limites exatos dependem de carga real observada
em produção (mesmo princípio já usado em `PARTITIONING.md`/`INDEXES.md`: a estrutura da política é
decidida agora, os valores são calibrados depois, nunca inventados sem dado). O que este documento
fixa é: **por quais dimensões o limite é aplicado** e **quais categorias de operação têm política
diferente** — isso não muda com o número escolhido.

## Dimensões (podem se combinar — o limite mais restrito vale)

| Dimensão | O que limita | Quando se aplica |
|---|---|---|
| Usuário | Ações de um Usuário autenticado específico | Toda chamada Web/Mobile autenticada |
| Tenant | Soma de todas as chamadas de todos os Usuários de um tenant | Protege contra um tenant único consumir capacidade desproporcional do serviço compartilhado |
| IP | Origem de rede da chamada | Principal defesa contra tentativa de força bruta em login, independente de autenticação |
| API Key | Uma chave de integração específica (`tokens_api`) | Toda chamada de API/Integração |
| Webhook | Entrega de webhook **de saída** (GestorFrete → tenant) | Não é limite de entrada — é o ritmo de retry, ver `WEBHOOKS.md` |
| Integração externa | Chamada do GestorFrete **para fora** (SEFAZ, ANTT, Asaas) | Respeita o rate limit do provedor externo, não o nosso — dimensão inversa das demais |

## Categorias de operação — por que cada uma precisa de um limite próprio

| Categoria | Motivo de ter política diferenciada |
|---|---|
| **Login** | Alvo direto de força bruta — limite mais agressivo por IP, independente de autenticação (não há Usuário ainda resolvido nesse ponto) |
| **Consulta** (`GET`) | Volume naturalmente alto (painel operacional, `viagens.tenant_id_status_operacional` é a query mais comum do sistema) — limite generoso, não deve incomodar uso normal |
| **Upload** (anexos, D024) | Custo de I/O/storage por chamada é maior que uma consulta simples — limite mais conservador que Consulta |
| **Exportação** (`exportacoes_geradas`) | Potencialmente cara (gera relatório grande) — candidata a `202 Accepted` assíncrono (`NAMING_CONVENTION.md` seção 7) em vez de só rate limit; limite por tenant, não só por usuário, para não deixar um relatório grande monopolizar capacidade |
| **API Pública** | Consumida por terceiros que a plataforma não controla — limite por API Key mais restrito que o tráfego interno do próprio ERP Web |
| **Webhook** (saída) | Não é "limite de entrada" — é o ritmo de retry/disparo, tratado em `WEBHOOKS.md`, nunca confundido com rate limit de requisição recebida |
| **App Motorista** | Uso offline-first (D039) — picos de sincronização em lote quando o motorista reconecta; limite precisa tolerar rajada maior que uso Web contínuo, não um limite uniforme por segundo |

## Resposta ao exceder o limite

```
429 Too Many Requests
Retry-After: 30
```

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Limite de requisições excedido. Tente novamente em instantes.",
    "details": [],
    "request_id": "..."
  }
}
```

`Retry-After` sempre presente (segundos até a próxima tentativa fazer sentido) — mesmo formato de
erro de `ERROR_MODEL.md`, nenhuma exceção de envelope só porque é `429`.

## Onde o limite é aplicado

Preferencialmente no **API Gateway** (`OPENAPI_ARCHITECTURE.md` seção 1), antes da requisição
alcançar o serviço FastAPI — mais barato (rejeita cedo) e centraliza a política num único lugar em
vez de espalhar lógica de limite em cada rota. Limite por dimensão de negócio fina (ex.: "máximo de
Viagens criadas por minuto por tenant", diferente de um rate limit genérico de requisições) pode
exigir lógica na Application quando o Gateway não tiver visibilidade de domínio suficiente — decisão
tomada endpoint a endpoint quando isso for genuinamente necessário, não como padrão.

## Como este documento cresce

Valores concretos (requisições/minuto por dimensão/categoria) são adicionados aqui como uma tabela
própria assim que a infraestrutura de produção existir para medir carga real — registrados como
decisão quando isso acontecer, nunca estimados especulativamente agora.
