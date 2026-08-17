# 031 — Maintenance Triggers (Gatilhos de Abertura)

Bounded context proprietário: `maintenance` (D215). **Documento sem endpoints** — gatilho é causa de
abertura, não um comando de usuário (D256); `ordens_servico.origem_abertura` já cobre integralmente
o vocabulário real, sem precisar de uma rota própria de "disparo".

## D256 — `origin` é origem, nunca substitui `status`

`origin` (`origem_abertura`) documenta **por que** a OS nasceu; `status` (máquina de estados,
`026-maintenance-orders.md`) documenta **onde ela está agora**. Os dois nunca se confundem: uma OS
`origin = VIAGEM_INTERROMPIDA` percorre exatamente a mesma máquina de estados de uma OS
`origin = MANUAL` — nenhuma transição, precondição ou comando depende de `origin`.

## Vocabulário real (Enum físico) — não o exemplo informal do pedido

O pedido deste lote listou, como exemplos conceituais, `KM`/`HORAS`/`DIAS`/`CALENDARIO`/`MOTOR`/
`TELEMETRIA`/`FABRICANTE` — esses são os **tipos de gatilho de um Plano de Manutenção Preventiva**
(`tipo_gatilho`, `029-preventive-maintenance-plans.md`), um enum diferente e mais granular do que
`origem_abertura` da OS. O Enum real de `origem_abertura` (`ordens_servico_origem_abertura_enum`,
`relational/005-manutencao.md`) tem só 5 valores — a granularidade de KM/HORAS/DIAS/CALENDARIO/MOTOR
colapsa em um único valor na OS, porque a OS só precisa saber *que* foi um Plano Preventivo que a
abriu, não qual tipo de gatilho específico (essa informação já vive no Plano referenciado
indiretamente, D226 — nenhum filtro/campo aqui reconstrói o que já está em outra tabela).

| `origin` (real, `ordens_servico`) | Conceito do pedido | Quem cria a OS com este valor | Endpoint próprio? |
|---|---|---|---|
| `MANUAL` | Usuário abre manualmente | `POST /ordens-servico` (`026`) | **Sim** — único valor aceito neste lote |
| `MANUTENCAO_PREVENTIVA_SUGERIDA` | KM/Horas/Dias/Calendário/Motor/Fabricante atingidos | Consumidor futuro do agendamento calculado a partir de `029` + `024-odometer-readings.md` | Não — fora de escopo |
| `VIAGEM_INTERROMPIDA` | Pane | Consumidor futuro do evento `ViagemInterrompida` (`freight`, já em `EVENT_MAP.md`) | Não — fora de escopo |
| `CHECKLIST_REPROVADO` | Checklist | Consumidor futuro do evento `ChecklistReprovado` (`007-CHECKLIST.md`, fluxo ainda não convertido em API) | Não — fora de escopo |
| `SUGESTAO_IA` | IA | Consumidor futuro de `Sugestão de IA` (`dictionary/012-ia.md`) | Não — fora de escopo |

## Por que nenhum `POST /maintenance/trigger` existe

O domínio não documenta um comando genérico de "disparar gatilho" em nenhum lugar
(`003-MANUTENCAO.md`, `RBAC_MATRIX.md` §7.9) — cada origem automática é, na prática, um consumidor
de evento interno criando uma OS via a mesma operação de escrita que `POST /ordens-servico` usa
(`origin` setado internamente pelo consumidor, nunca por um cliente HTTP externo). Inventar um
endpoint de gatilho genérico aqui seria inventar um comando que o domínio nunca especificou —
exatamente o que o usuário pediu para evitar. Quando cada consumidor automático for implementado
(Plano Preventivo, `ViagemInterrompida`, `ChecklistReprovado`, Sugestão de IA), ele provavelmente
chama a mesma camada de aplicação por trás de `POST /ordens-servico` internamente — decisão de
implementação de Backend, não de contrato de API pública.

## Fora de escopo, não esquecido

Os quatro consumidores automáticos (linhas 2 a 5 da tabela acima) — cada um depende de um módulo/
fluxo que ainda não tem API própria (`029` cobre só o cadastro do Plano, não a leitura periódica que
dispararia a criação automática; `007-CHECKLIST.md` não foi convertido; Sugestão de IA não tem
bounded context de API ainda).

## Como este documento cresce

Cada vez que um dos quatro consumidores automáticos ganhar implementação real, este documento ganha
uma seção descrevendo o mecanismo (evento consumido → OS criada com `origin` correspondente) — nunca
um novo endpoint público, salvo decisão explícita em contrário.
