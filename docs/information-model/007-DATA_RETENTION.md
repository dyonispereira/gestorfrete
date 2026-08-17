# 007 — Data Retention

Por quanto tempo guardar cada tipo de informação. Prazos legais são marcados **"a validar"**
explicitamente quando dependem de legislação específica (fiscal, trabalhista, LGPD) — nenhum prazo
jurídico é apresentado aqui como definitivo sem confirmação. Nenhum prazo aqui implica exclusão ao
final — implica **arquivamento** (D001, e ver [`005-DATA_LIFECYCLE.md`](./005-DATA_LIFECYCLE.md)).

## Tabela de retenção

| Tipo de dado | Retenção ativa proposta | Depois de expirar | Status |
|---|---|---|---|
| Logs de sistema/aplicação (técnicos, não de auditoria de negócio) | 90 dias | Descartável (não é dado de negócio, D001 não se aplica a log técnico puro) | Proposto |
| Fotos (checklist, avaria, canhoto, cupom de abastecimento) | Igual à retenção do documento/entidade que evidenciam (Canhoto segue CT-e; foto de checklist segue a Viagem) | Arquivamento junto com a entidade-mãe | Proposto |
| XML (CT-e, MDF-e) | Mínimo do prazo fiscal exigido — referência comumente citada de 5 anos para documentos fiscais eletrônicos no Brasil | Arquivamento a frio, nunca exclusão | **A validar juridicamente** |
| PDFs (DACTE/DAMDFE, relatórios gerados) | Igual ao XML correspondente, quando gerado a partir de documento fiscal; 2 anos para relatórios operacionais gerados sob demanda | Arquivamento | Proposto (relatórios) / **A validar** (fiscais) |
| Canhotos | Igual ao CT-e correspondente (é a prova de cumprimento do CT-e) | Arquivamento junto com a Viagem | **A validar** (segue prazo fiscal) |
| Rastreamento (Posição de Veículo — dado bruto) | Curta: proposta de 90 dias em granularidade bruta | Agregação estatística (velocidade média, km/dia) mantida permanentemente; dado bruto arquivado/descartado após agregação | Proposto — ver [`HIGH_VOLUME_ENTITIES.md`](./HIGH_VOLUME_ENTITIES.md) |
| Eventos (mensagens no barramento RabbitMQ, já processadas) | Dias (fila operacional, não é o registro histórico) | Descartado após confirmação de processamento — o registro permanente é o `StatusHistory` gerado a partir do evento (D017/D018), não a mensagem em si | Proposto |
| Auditoria (`audit`, trilha D007) | Mínimo igual à retenção do dado auditado — na prática, permanente para a maioria das entidades de negócio | Arquivamento a frio após período ativo longo (ex: 2 anos ativo + arquivado) | Proposto, prazo mínimo **a validar** conforme requisito de compliance |
| Financeiro (Contas a Pagar/Receber, Faturamento) | Referência comum de 5 anos, alinhada a prazos de prescrição/decadência tributária e contábil | Arquivamento a frio | **A validar juridicamente/contabilmente** |
| Fiscal (CT-e, MDF-e, CIOT, Carta de Correção) | Ver XML acima — mesmo prazo | Arquivamento | **A validar juridicamente** |
| Dados pessoais LGPD (CPF, CNH, endereço de pessoa física) | Enquanto durar a relação contratual + prazo legal aplicável — nunca indefinido, por princípio de minimização da própria LGPD | Anonimização ou exclusão quando a base legal para retenção deixar de existir | **A validar juridicamente** — ver [`../architecture/security-rbac-lgpd.md`](../architecture/security-rbac-lgpd.md) |
| Platform Reference Data (D046) | Permanente — não se aplica retenção/arquivamento no mesmo sentido (é Seed Data, D048) | Não aplicável | Definitivo |

## Princípios

- **"A validar" é uma categoria legítima, não uma lacuna** — este documento existe para deixar
  explícito o que já pode ser decidido tecnicamente (ex: log técnico não precisa de prazo jurídico)
  e o que exige confirmação jurídica/contábil antes da implementação (ex: prazo fiscal exato).
  Nenhum prazo "a validar" deve ser implementado como definitivo sem essa confirmação.
- **Retenção nunca é menor que a exigência legal aplicável** — quando houver conflito entre um
  prazo técnico conveniente e um prazo legal, o legal sempre vence.
- **Dado de Alto Volume tem estratégia diferenciada** (D049/D050): dado bruto de séries temporais
  (GPS, telemetria) é retido por muito menos tempo que o dado de negócio que ele sustenta — a
  agregação/derivação é o que se mantém no longo prazo, não o dado bruto.
- Consistente com [`005-DATA_LIFECYCLE.md`](./005-DATA_LIFECYCLE.md): todo prazo aqui é sobre
  quando um dado sai de "ativo" para "arquivado" — nunca sobre exclusão física (D001).

## Requisitos futuros

- Confirmação jurídica formal de todos os prazos marcados "a validar" antes da modelagem física do
  banco assumir qualquer um deles como definitivo.
- Política de exportação/anonimização de dado pessoal a pedido do titular (LGPD), com prazo de
  atendimento próprio.
