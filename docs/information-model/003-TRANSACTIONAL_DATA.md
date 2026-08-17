# 003 — Transactional Data

Quais entidades do GestorFrete são dado transacional (D036 — **Operacional**): criadas em volume,
mudam de estado ao longo de uma vida útil curta/média, e por isso exigem pensar em crescimento,
retenção e arquivamento desde já — diferente de Master Data ([`002-MASTER_DATA.md`](./002-MASTER_DATA.md)).

## Entidades transacionais

| Entidade | Bounded Context | Frequência de Criação | Frequência de Alteração | Expectativa de Crescimento | Retenção | Arquivamento |
|---|---|---|---|---|---|---|
| Viagem | `freight` | Alta (múltiplas por veículo/dia) | Alta (muda de status continuamente até `ENCERRADA`, ver [`../flows/002-VIAGEM.md`](../flows/002-VIAGEM.md)) | Muito alta — cresce com o número de tenants × frota; potencialmente milhões de registros em poucos anos | Permanente (D001) | A frio após N anos de `ENCERRADA` (prazo em `007-DATA_RETENTION.md`) |
| Ordem de Serviço | `maintenance` | Média | Média | Média | Permanente | Idem |
| Abastecimento | `freight` | Alta | Baixa (após `VALIDADO`, raramente muda) | Alta | Permanente | Idem |
| Checklist | `maintenance` | Alta (a cada viagem/OS) | Baixa (imutável após `APROVADO`/`REPROVADO`, D016) | Alta | Permanente | Idem |
| CT-e | `documents` | Alta (tipicamente um por viagem) | Baixa (só muda por cancelamento/carta de correção) | Alta | Permanente — obrigação fiscal (prazo legal, ver `007-DATA_RETENTION.md`) | Sujeito a prazo legal, não só operacional |
| MDF-e | `documents` | Alta | Baixa | Alta | Permanente — obrigação fiscal | Idem |
| Conta a Receber | `financial` | Alta | Média (muda de status até `RECEBIDA`) | Alta | Permanente | A frio após quitação + prazo fiscal |
| Conta a Pagar | `financial` | Alta | Média | Alta | Permanente | Idem |

## Casos de altíssimo volume a observar

Duas fontes de dado não estão na lista original, mas crescem muito mais rápido que qualquer
entidade acima e merecem atenção antecipada na modelagem física futura:

- **Posição de Veículo** (`tracking`, ver [`../flows/008-RASTREAMENTO.md`](../flows/008-RASTREAMENTO.md)):
  potencialmente uma linha a cada poucos segundos por veículo em movimento — ordens de grandeza
  acima de qualquer entidade transacional de negócio. Retenção detalhada (dado bruto vs. eventos
  derivados) é crítica aqui — ver `007-DATA_RETENTION.md`.
- **Trilha de Auditoria** (`audit`, D007): cresce com toda transição de status de toda entidade do
  sistema (D017/D018) — segundo maior volume esperado depois de Posição de Veículo.

## Classificação de atributos e qualidade (D043–D045)

Dado transacional é onde as três decisões desta revisão mais se aplicam, porque o mesmo dado pode
chegar por caminhos muito diferentes dentro da mesma entidade:

- **Natureza do atributo (D043)**: por exemplo, na Viagem, `motorista_id` é **Informado** (o Gestor
  escolhe), a posição atual é **Capturada** (rastreador), a Margem Realizada é **Calculada**
  (D041), e — futuramente — um CT-e de um sistema legado migrado seria **Importado**.
- **Qualidade (D044)**: uma Viagem pode existir sem Canhoto (Entrega ainda em aberto) — a
  informação existe, mas a qualidade documental dela é `Parcial`, não `Inconsistente`. O indicador
  de qualidade não bloqueia a operação (a Viagem continua funcionando) — ele **descreve** o estado
  do dado para dashboards e para priorização de correção.
- **Confiança (D045)**: a mesma Leitura de Hodômetro (ver [`../domain/003-frota.md`](../domain/003-frota.md))
  pode ter confiança `Alta` (telemetria futura), `Média` (informada no Checklist) ou `Baixa`
  (digitada manualmente pelo motorista) — o valor usado para decisão automática (ex: disparar
  manutenção preventiva) deve poder considerar essa confiança, não tratar todas as origens como
  equivalentes.

Estas três classificações não têm campo formal em nenhuma entidade ainda — ficam registradas aqui
como decisão de princípio (D043–D045); a aplicação campo a campo é trabalho de
`DATA_DICTIONARY_FUNCTIONAL.md` (a ser escrito, próxima etapa após o Information Model — ver
[`../product/DECISIONS.md`](../product/DECISIONS.md)).

## Regras gerais de retenção e arquivamento

- Nenhuma entidade transacional é excluída fisicamente (D001) — "arquivamento" aqui significa
  mover para armazenamento mais frio/barato, nunca apagar.
- Documentos fiscais (CT-e, MDF-e) têm prazo de retenção determinado por legislação, não por
  política interna — tratado com "a validar" em `007-DATA_RETENTION.md` até confirmação jurídica.
- Detalhamento completo do ciclo de vida (não apenas retenção) de cada uma destas entidades está em
  [`005-DATA_LIFECYCLE.md`](./005-DATA_LIFECYCLE.md) (a ser escrito).
