# 083 — Timelines (Linha do Tempo Universal)

Bounded context proprietário: nenhum próprio — cada Timeline pertence ao Aggregate Root que a
possui (D215 aplicado por dono, mesmo padrão de `080`/`081`).

## D318 — Timeline é sempre read model, nunca uma tabela

Não existe `timelines` em nenhum arquivo `relational/` e nenhuma linha deste contrato cria uma —
Timeline Universal (D022, D187) é uma **projeção composta em tempo de leitura**, combinando, para
um Aggregate Root específico:

- histórico de status (`*_status_history`, quando o agregado tiver máquina de estados);
- eventos de domínio publicados por aquele agregado (`EVENT_MAP.md`);
- Anexos e Comentários vinculados (`080-attachments.md`/`081-comments.md`, D186);
- entradas específicas do próprio domínio (ex.: mudanças de alocação de recursos da Viagem).

Nunca uma tabela própria armazenando o resultado já montado — cada consulta recompõe a partir das
fontes acima.

## Único dono com endpoint implementado: Viagem

`019-trip-timeline.md` (Lote 4) é a única Timeline Universal com endpoint hoje —
`GET /api/v1/viagens/{id}/timeline` — e já documentava explicitamente, em sua própria tabela de
fontes, que Anexos/Comentários **ainda não estavam incluídos** por não terem endpoint de API. Com
`080`/`081` fechados neste lote, essa lacuna específica pode ser fechada dentro de `019` (ver "Como
este documento cresce" abaixo) — mas isso é uma edição em `019-trip-timeline.md`, não um novo
endpoint aqui.

## Padrão para novos donos

Qualquer entidade cujo Data Dictionary Funcional já a marca como "Dono da Timeline" segue o mesmo
contrato de `019-trip-timeline.md`: `GET /{recurso}/{id}/timeline`, cursor-paginado (D187, mesma
categoria de Time Series/History), cada entrada com `type`/`occurred_at`/`summary`/referência à
fonte original — nunca um schema novo por dono.

## Fora de escopo, não esquecido

Praticamente toda entidade rica do sistema declara um "Dono da Timeline" no Domain Model (Ordem de
Serviço, Assinatura, CT-e, Convite, Webhook, etc.) — nenhuma delas ganha um endpoint de Timeline
nesta preparação além de Viagem (já existente desde o Lote 4). `030-maintenance-history.md`
(Ordem de Serviço) é um caso adjacente mas deliberadamente distinto: expõe só o histórico
*operacional* de status, nunca a Timeline completa (D241, decisão já registrada no Lote 6) — não
alterado por este lote.

## Como este documento cresce

Ativar Timeline para um novo dono é: (1) confirmar que o Data Dictionary Funcional já o declara
"Dono da Timeline"; (2) adicionar `GET /{recurso}/{id}/timeline` ao arquivo do dono (nunca aqui);
(3) registrar a nova rota em `components/security.md`. Este documento nunca ganha endpoints
próprios — é a definição do padrão, não uma implementação.
