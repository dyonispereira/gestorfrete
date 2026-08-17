# 010 — App Motorista

## Objetivo

Documentar a experiência mobile do Motorista — do login à sincronização final de uma viagem — e o
módulo **Meu Desempenho**, que transforma dados operacionais já capturados em autoconhecimento para
o motorista, não apenas em controle para a transportadora. Este fluxo não tem máquina de estados
própria (ver [`INDEX.md`](./INDEX.md)): ele é a superfície mobile que executa e consome as máquinas
de estado de [`002-VIAGEM.md`](./002-VIAGEM.md), [`006-ABASTECIMENTO.md`](./006-ABASTECIMENTO.md) e
[`007-CHECKLIST.md`](./007-CHECKLIST.md).

## Pré-condições

- Motorista cadastrado, com credenciais de acesso ao app.
- Ao menos uma Viagem atribuída para haver o que executar.

## Gatilho inicial

Motorista abre o app e realiza login.

## Fluxo principal

1. **Login** — autenticação do motorista (fundação de segurança ainda não implementada, ver
   [`../architecture/security-rbac-lgpd.md`](../architecture/security-rbac-lgpd.md)).
2. **Download da viagem** — dados da Viagem atribuída (rota, carga, cliente, checklist pendente)
   baixados para uso offline.
3. **Modo offline** — o app opera com os dados baixados mesmo sem conectividade: checklist,
   registro de coleta/entrega, fotos e assinatura ficam armazenados localmente até sincronizar.
4. **Execução em campo** — checklist (ver [`007-CHECKLIST.md`](./007-CHECKLIST.md)), coleta, GPS
   (ver [`008-RASTREAMENTO.md`](./008-RASTREAMENTO.md)), abastecimento (ver
   [`006-ABASTECIMENTO.md`](./006-ABASTECIMENTO.md)), ocorrências, entregas.
5. **Fotos** — capturadas em pontos obrigatórios (checklist, avaria, canhoto, cupom de
   abastecimento), armazenadas localmente até upload.
6. **Upload** — fotos e dados enviados ao servidor assim que houver conectividade.
7. **Assinatura** — coleta da assinatura digital do destinatário no momento da entrega.
8. **OCR** — leitura automática de texto em cupons fiscais/canhotos fotografados, reduzindo
   digitação manual (consistente com o princípio de reduzir trabalho humano — ver
   [`../product/VISION.md`](../product/VISION.md), capítulo 6).
9. **Canhotos** — comprovante de entrega (foto + assinatura) registrado.
10. **Fim da viagem** — motorista confirma a conclusão; Viagem avança para `FINALIZADA` (Status
    Operacional, ver [`002-VIAGEM.md`](./002-VIAGEM.md)) quando as condições são atendidas.
11. **Sincronização** — todos os dados pendentes (ainda não enviados durante a execução offline)
    são enviados ao servidor em lote.

## Módulo Meu Desempenho

Superfície de autoconhecimento do motorista, alimentada por dados que o sistema já captura em
outros fluxos — nenhum dado novo é coletado especificamente para este módulo:

| Indicador | Origem |
|---|---|
| Média de combustível | [`006-ABASTECIMENTO.md`](./006-ABASTECIMENTO.md) — média km/litro validada |
| Quilômetros percorridos | [`008-RASTREAMENTO.md`](./008-RASTREAMENTO.md) |
| Viagens concluídas | [`002-VIAGEM.md`](./002-VIAGEM.md) — Status Operacional `FINALIZADA` |
| Entregas realizadas | [`002-VIAGEM.md`](./002-VIAGEM.md) — Entregas em estado terminal `Concluída` |
| Pontuação de direção | Telemetria (`tracking`/`telemetry` — requisito futuro, ver Requisitos futuros) |
| Eventos de excesso de velocidade | [`008-RASTREAMENTO.md`](./008-RASTREAMENTO.md) — `VelocidadeExcedidaDetectada` |
| Frenagens bruscas | Telemetria (requisito futuro — depende de sensor de aceleração, não apenas GPS) |
| Tempo ocioso | [`008-RASTREAMENTO.md`](./008-RASTREAMENTO.md) — Paradas não planejadas |
| Ranking interno | Comparativo entre motoristas do mesmo tenant — **opt-in**, habilitado pela transportadora, nunca exposto por padrão |

O ranking interno é uma configuração de tenant (D010 aplicado por analogia: nada que exponha
comparativamente o desempenho de um motorista a outros é ativado sem decisão explícita da
transportadora) — por padrão, desabilitado.

## Fluxos alternativos

- **Uso 100% offline por período prolongado** (área rural sem cobertura por dias): o app continua
  operando com os dados já baixados; a viagem só reflete no servidor após reconexão.
- **Ranking desabilitado**: Meu Desempenho mostra os indicadores individuais do motorista
  normalmente, apenas sem a comparação com outros motoristas.

## Fluxos de exceção

- **Falha de sincronização**: dados pendentes não conseguem ser enviados (conectividade instável
  intermitente) — o app tenta novamente automaticamente, sem perda de dado local até confirmação de
  recebimento pelo servidor (nunca apaga o dado local antes do ACK do servidor).
- **Conflito de dados** (mesma viagem operada por dois dispositivos, ex: troca de aparelho em
  campo): o servidor aplica a mesma disciplina de D017/D018 — cada evento é um novo registro,
  nunca uma sobrescrita; conflitos reais (ex: dois checklists diferentes para o mesmo ponto) geram
  Ocorrência para revisão humana.
- **OCR falha ou lê incorretamente**: fallback para digitação manual pelo motorista — o app nunca
  bloqueia o fluxo esperando um OCR perfeito.
- **Foto corrompida no upload**: nova tentativa de envio; se persistir, o app sinaliza a
  necessidade de recaptura antes de permitir avançar em pontos obrigatórios (ex: canhoto).

## Eventos publicados

| Evento | Gerado quando |
|---|---|
| `ViagemBaixadaOffline` | Download de viagem para uso offline (novo) |
| `FotoCapturada` | Foto registrada localmente (novo) |
| `FotoSincronizada` | Upload de foto concluído (novo) |
| `AssinaturaColetada` | Assinatura digital do destinatário capturada (novo) |
| `OCRProcessado` | Leitura automática de um documento fotografado concluída (novo) |
| `SincronizacaoConcluida` | Todos os dados pendentes enviados com sucesso (novo) |
| `SincronizacaoFalhou` | Tentativa de sincronização não concluída (novo) |

## Eventos consumidos

| Evento | Publicado por | Efeito no App Motorista |
|---|---|---|
| `ViagemCriada` / `ViagemDespachada` | `freight` | Nova viagem disponível para download |
| `ChecklistReprovado` | `maintenance` | Bloqueia início da viagem no app |
| `AbastecimentoValidado`/`AbastecimentoSuspeito` | `maintenance`/`freight` | Reflete no histórico do motorista |
| `VelocidadeExcedidaDetectada` | `tracking` | Alimenta Meu Desempenho |

## Permissões

| Etapa | Quem executa |
|---|---|
| Todo o fluxo | Motorista, restrito às suas próprias viagens (ver [`../product/PERSONAS.md`](../product/PERSONAS.md), persona 9) |
| Configuração do ranking interno (habilitar/desabilitar) | Diretor / Gestor Operacional (nível de tenant) |
| Consulta somente leitura a dados de qualquer motorista | Auditor |

## Auditoria

Login, upload de dados e qualquer atualização manual (ex: correção de OCR) são registrados em
`audit`, com ator e timestamp (D007).

## Notificações

- Motorista: nova viagem atribuída, sincronização pendente, falha de sincronização persistente.
- Gestor Operacional: motorista sem sincronizar há mais tempo que o esperado (possível problema de
  conectividade ou de dispositivo).

## Capacidades Transversais

1. **Timeline Universal** (D022): eventos do app (download, fotos, assinatura, sincronização)
   integram a Timeline Universal da Viagem (ver [`002-VIAGEM.md`](./002-VIAGEM.md)) — não têm
   timeline própria separada.
2. **Comentários** (D023): não aplicável ao app do motorista diretamente — comentários sobre a
   viagem ficam no Portal do Gestor.
3. **Anexos** (D024): fotos de checklist, avaria, canhoto e cupom de abastecimento são o principal
   tipo de anexo gerado por este fluxo.
4. **Favoritos** (D025): não aplicável — o app mostra apenas a viagem ativa do motorista, não há
   necessidade de favoritar.
5. **Pesquisa Global** (D026): não aplicável — o motorista não realiza busca global, apenas navega
   sua própria viagem ativa.

## Regras de negócio relacionadas

- D007 — auditoria obrigatória.
- D010 — nenhuma operação crítica sem confirmação (ex: confirmar fim da viagem).
- D017/D018 — eventos do app nunca sobrescrevem dado local ou remoto, sempre novos registros.
- D022–D026 — capacidades transversais aplicadas na seção acima (a maioria não aplicável a este
  fluxo especificamente, por sua natureza mobile/operacional restrita).

## SLA

| Etapa | Prazo |
|---|---|
| Download da viagem após atribuição | Imediato, quando há conectividade |
| Sincronização após reconexão | Automática, em background, sem ação do motorista |
| Upload de foto individual | A definir (depende de tamanho/qualidade da conexão) |

## Indicadores Gerados

- Todos os listados em Meu Desempenho (combustível, km, viagens, entregas, velocidade, tempo
  ocioso).
- Tempo médio de sincronização após reconexão.
- Taxa de falha de sincronização.
- Adoção do app (motoristas ativos vs. cadastrados).

## Riscos

- Conectividade instável prolongada atrasando a visibilidade da operação para o Gestor.
- Perda de dado local por falha do dispositivo antes da sincronização (mitigado por não apagar
  dado local sem ACK do servidor).
- Ranking interno mal configurado gerando pressão negativa em vez de engajamento — risco de
  produto, a ser observado no primeiro uso real.
- Dependência de OCR sem fallback manual claro para o motorista.

## KPIs impactados

- Adoção do app pelo motorista (ver [`../product/VISION.md`](../product/VISION.md), capítulo 32).
- Tempo entre entrega física e registro no sistema.
- Percentual de canhotos com foto + assinatura completos.

## Critérios de encerramento

- Não há encerramento próprio — o app acompanha o ciclo de vida da Viagem em execução; "concluído"
  para uma viagem específica é o `SincronizacaoConcluida` após `ViagemConcluida`.

## Pontos de integração

- `freight`, `maintenance` (checklist, abastecimento), `tracking` (posição), `documents`
  (canhoto), `drivers` (perfil do motorista).
- Serviço de OCR (fora do escopo eletrônico desta fundação).

## Requisitos futuros

- Telemetria veicular (frenagem brusca, aceleração) via `telemetry`, para completar a Pontuação de
  Direção do Meu Desempenho.
- Gamificação opcional (metas, conquistas) além do ranking simples.
- Chat direto motorista-gestor dentro do app, reduzindo dependência de canais externos (WhatsApp).
