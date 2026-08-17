# 005 — Data Lifecycle

Como os dados nascem, evoluem e terminam. Este documento descreve o **padrão geral** de ciclo de
vida e aponta, para cada dado Nível 3 (Operação, D047), ao documento canônico (D035) onde a máquina
de estados real já está definida — não redefine nada.

## O padrão geral (todo dado Nível 2/3)

```
Criação → Uso ativo (transições de status) → Encerramento → Retenção ativa → Arquivamento
```

- **Criação**: o dado nasce por ação de usuário (Informado, D043) ou por captura/integração
  (Capturado/Importado, D043).
- **Uso ativo**: o dado passa pela sua máquina de estados (D015/D016), acumulando histórico
  append-only (D017/D018) — nunca sobrescrito.
- **Encerramento**: o dado atinge um estado terminal (ex: Viagem `ENCERRADA`, D019; OS `FECHADA`).
  Isto **não** é o fim do dado — apenas o fim de sua fase operacional ativa.
- **Retenção ativa**: mesmo encerrado, o dado permanece em armazenamento de acesso normal por um
  período (ver [`007-DATA_RETENTION.md`](./007-DATA_RETENTION.md)), consultável para operação do
  dia a dia, relatórios recentes e auditoria.
- **Arquivamento**: após o período de retenção ativa, o dado é movido para armazenamento mais
  frio/barato — **nunca excluído fisicamente** (D001). Arquivamento é uma decisão de
  performance/custo de infraestrutura, não uma decisão sobre o dado em si.

Dados Nível 1 (Plataforma, D046/D047) não seguem este padrão — são Seed Data (D048): nascem com a
implantação do sistema/migração, raramente mudam, e não são "encerrados" nem "arquivados" no mesmo
sentido.

## Ciclo do Financeiro/Fiscal da Viagem (fluxo mais complexo do sistema)

```
Cotação → Aprovada → Programada → Executada → Faturada → Recebida → Encerrada → Histórico → Arquivamento
```

Já documentado em detalhe, sem redefinição aqui (D035):
- Máquina de estados Operacional/Fiscal/Financeiro/`ENCERRADA`:
  [`../flows/002-VIAGEM.md`](../flows/002-VIAGEM.md).
- Separação Previsto/Realizado e o ciclo financeiro propriamente dito:
  [`../flows/005-FINANCEIRO.md`](../flows/005-FINANCEIRO.md).
- Ciclo fiscal (CT-e/MDF-e/CIOT): [`../flows/009-FISCAL.md`](../flows/009-FISCAL.md).

## Outros ciclos de vida já documentados (referência, não redefinição — D035)

| Dado | Documento canônico |
|---|---|
| Ordem de Serviço | [`../flows/003-MANUTENCAO.md`](../flows/003-MANUTENCAO.md) |
| Pneu | [`../flows/004-PNEUS.md`](../flows/004-PNEUS.md) |
| Checklist | [`../flows/007-CHECKLIST.md`](../flows/007-CHECKLIST.md) |
| Abastecimento | [`../flows/006-ABASTECIMENTO.md`](../flows/006-ABASTECIMENTO.md) |
| Tenant / Assinatura | [`../flows/001-ONBOARDING.md`](../flows/001-ONBOARDING.md) |

## Política de retenção e arquivamento

Prazos específicos por tipo de dado estão em
[`007-DATA_RETENTION.md`](./007-DATA_RETENTION.md) — este documento define **o padrão de
transição** (quando um dado sai de "ativo" para "arquivado"), aquele define **por quanto tempo**.

Regras gerais válidas para todo o sistema:

- Arquivamento nunca é exclusão (D001) — é sempre reversível em princípio (dado ainda existe, só
  está em um tier de armazenamento diferente).
- Dado de Alto Volume/Time Series (D049/D050 — ver
  [`HIGH_VOLUME_ENTITIES.md`](./HIGH_VOLUME_ENTITIES.md)) tem política de arquivamento mais
  agressiva que dado transacional comum, por volume, não por importância.
- Dado Fiscal/Financeiro segue prazo legal quando aplicável (marcado "a validar" em
  `007-DATA_RETENTION.md` até confirmação jurídica), nunca um prazo interno menor que o exigido por
  lei.

## Requisitos futuros

- Job automatizado de arquivamento por política, executado quando a modelagem física existir.
- Política de restauração de dado arquivado sob demanda (ex: para uma auditoria antiga).
