# 008 — Rastreamento

## Objetivo

Documentar como a posição de um veículo é capturada, validada e transformada em eventos de negócio
(parada, desvio, velocidade, geofence) — **sem depender de uma única origem de localização**. Este
fluxo não gira em torno de uma máquina de estados de entidade (ver [`INDEX.md`](./INDEX.md)): é um
fluxo de eventos contínuo, consumido por [`002-VIAGEM.md`](./002-VIAGEM.md) e por
[`006-ABASTECIMENTO.md`](./006-ABASTECIMENTO.md) (validação de posição do posto), entre outros.

## Pré-condições

- Veículo com ao menos uma origem de localização configurada.
- Viagem em estado operacional ativo, para eventos vinculados a uma viagem específica (posições de
  pátio, fora de viagem, também são capturadas, sem vínculo).

## Gatilho inicial

Qualquer origem de localização emite uma nova posição para um veículo.

## Múltiplas Origens de Localização

Este fluxo **nunca assume GPS como única fonte**. Toda Posição carrega explicitamente sua origem e
um nível de confiabilidade:

| Origem | Confiabilidade padrão | Características |
|---|---|---|
| `RASTREADOR_API` | Alta | Hardware dedicado no veículo, integrado via API do fornecedor de rastreamento; frequência regular mesmo sem viagem ativa |
| `APP_MOTORISTA` | Média | GPS do celular do motorista, via [`010-APP_MOTORISTA.md`](./010-APP_MOTORISTA.md); sujeito a gaps quando o app está em segundo plano ou sem conectividade |
| `ELD` | Alta | Electronic Logging Device — integração futura, ainda não disponível no mercado brasileiro na mesma medida que em outros países; reservado para quando existir |
| `MANUAL` | Baixa | Atualização manual autorizada por um Gestor Operacional (ex: veículo em área sem cobertura por dias) — **sempre auditada**, nunca aceita silenciosamente |
| `IOT` | A definir | Dispositivos IoT futuros (sensores de carga, telemetria veicular) |

**Regra de precedência**: quando mais de uma origem reporta posições para o mesmo veículo em uma
janela de tempo próxima, prevalece a de maior confiabilidade para fins de cálculo de rota
percorrida e velocidade — as demais são preservadas no histórico (D017/D018), não descartadas.

## Fluxo principal

1. **Captura** — uma origem emite uma nova Posição (latitude, longitude, timestamp, velocidade,
   origem, confiabilidade).
2. **Heartbeat** — independente de haver movimento, a origem `RASTREADOR_API`/`ELD` emite um sinal
   periódico de "ativo"; ausência de heartbeat além de um limite gera alerta de perda de sinal (ver
   Riscos e [`002-VIAGEM.md`](./002-VIAGEM.md), Riscos).
3. **Geofence** — a posição é avaliada contra cercas virtuais cadastradas (pátio, cliente, zona
   restrita); cruzar uma cerca gera evento de Entrada/Saída.
4. **Paradas** — intervalo sem deslocamento acima de um limite configurável gera uma Parada,
   classificada como planejada (descanso, carregamento) ou não planejada.
5. **Desvios** — posição fora do corredor da rota planejada (ver `routing`, fundação futura) gera
   evento de desvio.
6. **Velocidade** — posição com velocidade acima do limite configurado (via/regulatório ou política
   da transportadora) gera evento de excesso de velocidade.
7. **Alertas** — os eventos acima, quando relevantes, geram notificação ao Gestor Operacional.

## Fluxos alternativos

- **Veículo sem viagem ativa**: posições continuam sendo capturadas (pátio, deslocamento
  administrativo), sem vínculo a uma Viagem — usadas para localização geral da frota.
- **Atualização manual em lote**: Gestor Operacional registra posições retroativas para um período
  sem sinal, cada uma marcada `MANUAL`/confiabilidade Baixa, com justificativa obrigatória.

## Fluxos de exceção

- **Perda de sinal prolongada**: ausência de heartbeat além do limite → alerta imediato; se ocorrer
  durante uma viagem em `EM_TRANSITO`, é registrado como risco operacional na própria Viagem (ver
  [`002-VIAGEM.md`](./002-VIAGEM.md), Riscos), sem necessariamente mover a Viagem para
  `INTERROMPIDA` (essa decisão cabe ao Gestor, avaliando o caso).
- **Conflito entre origens**: duas origens reportam posições incompatíveis para o mesmo veículo no
  mesmo instante — prevalece a de maior confiabilidade (ver Regra de precedência); a divergência é
  registrada, não descartada, para investigação (possível indício de uso indevido do veículo).
- **Suspeita de spoofing/fraude de posição**: padrão de posição fisicamente improvável (salto de
  distância incompatível com o tempo decorrido) → gera Ocorrência para investigação, mesma lógica de
  `SUSPEITO` usada em [`006-ABASTECIMENTO.md`](./006-ABASTECIMENTO.md).

## Eventos publicados

| Evento | Gerado quando |
|---|---|
| `PosicaoRegistrada` | Nova posição capturada de qualquer origem (novo) |
| `HeartbeatRecebido` | Sinal periódico de atividade recebido (novo) |
| `PerdaDeSinalDetectada` | Heartbeat ausente além do limite configurado (novo) |
| `GeofenceEntrada` / `GeofenceSaida` | Veículo cruza uma cerca virtual cadastrada (novo) |
| `ParadaIniciada` / `ParadaEncerrada` | Início/fim de um intervalo sem deslocamento acima do limite (novo) |
| `DesvioDeRotaDetectado` | Posição fora do corredor da rota planejada (novo) |
| `VelocidadeExcedidaDetectada` | Velocidade acima do limite configurado (novo) |

## Eventos consumidos

Nenhum — este fluxo é uma fonte primária de eventos, não um consumidor.

## Permissões

| Etapa | Quem executa |
|---|---|
| Captura automática (`RASTREADOR_API`, `ELD`, `IOT`) | Sistema, sem intervenção humana |
| Captura via app | Motorista (implícito, ao manter o app ativo) |
| Atualização manual | Gestor Operacional, sempre auditada |
| Cadastro de geofences, limites de velocidade | Gestor Operacional / Analista de Frota |
| Consulta somente leitura | Auditor |

## Auditoria

Toda posição `MANUAL` é auditada com ator e justificativa obrigatória (D007); posições automáticas
são auditadas apenas quanto à origem/confiabilidade, não exigem justificativa por serem
sistêmicas.

## Notificações

- Gestor Operacional: perda de sinal, desvio de rota, excesso de velocidade, parada não planejada
  prolongada.

## Capacidades Transversais

1. **Timeline Universal** (D022): eventos de posição relevantes (geofence, paradas, desvios,
   velocidade) alimentam a Timeline Universal da Viagem associada (ver
   [`002-VIAGEM.md`](./002-VIAGEM.md)) — posições brutas (alta frequência) não entram na timeline
   apresentada ao usuário, apenas os eventos derivados.
2. **Comentários** (D023): aplicável a uma Parada ou Desvio específico, para registrar contexto
   (ex: parada para descanso obrigatório); visibilidade interna.
3. **Anexos** (D024): não aplicável diretamente a posições individuais.
4. **Favoritos** (D025): mapas/filtros como "veículos parados há mais de 2h" favoritáveis pelo
   Gestor Operacional.
5. **Pesquisa Global** (D026): placa do veículo (retorna a última posição conhecida e sua origem/
   confiabilidade).

## Regras de negócio relacionadas

- D007 — auditoria obrigatória em atualização manual.
- D017/D018 — princípio de nunca descartar dado (aplicado aqui a posições de origens conflitantes,
  não apenas a status).
- D022–D026 — capacidades transversais aplicadas na seção acima.

## SLA

| Etapa | Prazo |
|---|---|
| Frequência mínima de posição em movimento (`RASTREADOR_API`/`ELD`) | A definir por plano/fornecedor |
| Heartbeat máximo sem posição antes de alertar perda de sinal | A definir (ex: 15 minutos, sujeito a ajuste por região de cobertura) |
| Processamento de geofence/velocidade/desvio | Near real-time (segundos) |

## Indicadores Gerados

- Percentual de tempo com sinal ativo, por veículo
- Velocidade média por trecho/viagem
- Número de paradas não planejadas por viagem
- Desvios de rota por viagem
- Tempo parado vs. em movimento (alimenta [`002-VIAGEM.md`](./002-VIAGEM.md), Indicadores Gerados)

## Riscos

- Perda de sinal prolongada (área rural sem cobertura).
- GPS impreciso em ambiente urbano denso/túneis.
- Dependência de uma única origem de baixa confiabilidade (`APP_MOTORISTA` isolado, sem
  `RASTREADOR_API`) para decisões operacionais críticas.
- Spoofing/fraude de posição.
- Atualizações manuais em excesso, mascarando problema real de cobertura de rastreador.

## KPIs impactados

- Disponibilidade de rastreamento (percentual de veículos com sinal ativo).
- Tempo parado vs. produtividade (ver [`002-VIAGEM.md`](./002-VIAGEM.md)).

## Critérios de encerramento

- Não há encerramento — fluxo contínuo enquanto o veículo estiver em operação.

## Pontos de integração

- Mapbox (mapa e roteirização), fornecedor de rastreamento veicular (API), App Motorista
  (`mobile`), `freight` (vínculo com Viagem ativa).

## Requisitos futuros

- Integração ELD quando disponível no mercado brasileiro.
- Dispositivos IoT para telemetria veicular (temperatura de carga refrigerada, abertura de baú).
- IA prevendo desvios/atrasos a partir do padrão histórico de rota (ver
  [`../product/VISION.md`](../product/VISION.md), capítulo 24).
