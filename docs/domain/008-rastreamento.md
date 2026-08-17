# 008 — Rastreamento

Entidades do bounded context `tracking` — observação de posição e telemetria de veículos, agnóstica
de fornecedor (Omnilink, Sascar, Autotrac, Positron, OnixSat, Cobli, Maxtrack ou qualquer outro).
Template completo de 22 campos (ver [`README.md`](./README.md)).

## Princípio fundamental (D116): rastreamento é observacional

`tracking` nunca altera diretamente o estado operacional de outro bounded context. Ele observa
(posição, telemetria, eventos detectados) e publica eventos — quem decide o significado de negócio
é sempre o dono da entidade afetada, consumindo o evento:

```
Posição recebida (tracking observa)
        ↓
PosicaoRegistrada (tracking publica)
        ↓
freight decide: "chegou ao destino" / "continua em trânsito" (nunca o inverso)
```

Isso é a mesma disciplina de D032 (bounded contexts não sabem quem consome seus eventos) aplicada
com ênfase específica a `tracking`, porque é o primeiro módulo cujo papel inteiro é observar
sistemas de terceiros — a tentação de "decidir" diretamente pela Viagem seria um vazamento de
responsabilidade grave.

## Reconciliação de nomes (D076)

A lista original em `ENTITY_CATALOG.md` (Posição de Veículo, Origem de Localização, Heartbeat,
Geofence, Parada de Veículo, Desvio de Rota, Evento de Velocidade, Configuração de Limite de
Velocidade — 8 entidades) foi escrita antes de existir a exigência explícita de agnosticismo de
fornecedor e da separação Posição × Telemetria desta rodada. Reconciliada:

| Original | Decisão | Por quê |
|---|---|---|
| Parada de Veículo, Desvio de Rota, Evento de Velocidade | **Consolidadas em uma única entidade: `Evento de Rastreamento`**, com `TIPO` como Enum | Três entidades quase idênticas (mesma estrutura: veículo, momento, dado detectado) — mesmo princípio já usado em `Ocorrência` (`002-operacao.md`): um tipo fechado, não uma entidade por tipo de evento. Evita o mesmo acúmulo de sinônimos que D076 existe para prevenir |
| Posição de Veículo, Origem de Localização, Geofence, Configuração de Limite de Velocidade | Mantidas | Já corretas, sem alteração |
| — | **Novas, exigidas pela diretriz de agnosticismo de fornecedor**: `Provedor de Rastreamento`, `Equipamento de Rastreamento` | Sem uma entidade que abstraia o fornecedor, o domínio ficaria implicitamente acoplado a um rastreador específico — exatamente o que a diretriz pede para evitar |
| — | **Nova, exigida pela separação explícita Posição × Telemetria**: `Leitura de Telemetria` | Ignição/velocidade/bateria/tensão/odômetro/horímetro/RPM/temperatura/combustível/aceleração/frenagem nunca devem viver dentro de `Posição de Veículo` (que é só Veículo+Lat+Long+Data/Hora+Fonte) |

Resultado: **9 entidades** (não as 8 originais) — crescimento real do domínio, não inflação.

---

## Provedor de Rastreamento

- **Objetivo**: Catálogo dos fornecedores de rastreamento integrados (Omnilink, Sascar, Autotrac,
  Positron, OnixSat, Cobli, Maxtrack, etc.) — a peça que torna o domínio agnóstico de fornecedor.
- **Responsabilidades**: Ser referenciado por Equipamento de Rastreamento; guardar apenas metadados
  de negócio do fornecedor (nome, contrato), nunca detalhes técnicos de protocolo de integração
  (isso é `infrastructure`, fora do domínio).
- **O que não faz**: Não implementa a integração em si — a lógica de tradução do protocolo
  específico de cada fornecedor para o modelo agnóstico do domínio vive na camada de
  infraestrutura (adapters), nunca aqui.
- **Aggregate Root**: Sim — entidade de **Referência** (D036).
- **Bounded Context proprietário**: `tracking`
- **Principais relacionamentos**: Equipamento de Rastreamento (1:N).
- **Eventos que publica**: `ProvedorDeRastreamentoCadastrado` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: nome único por tenant.
- **Regras de negócio associadas**: D001, D005/D006, D116 (o domínio nunca depende de um fornecedor
  específico — qualquer regra de negócio referencia `Equipamento`/`Posição`/`Evento`, nunca
  "Omnilink" diretamente).
- **Estados**: `Ativo` / `Inativo`.
- **Auditoria**: D007.
- **Linha do tempo**: cadastro, alterações.
- **Anexos suportados**: contrato com o fornecedor (D024).
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: métricas de confiabilidade por fornecedor (uptime, latência
  média de posição — calculadas em `analytics`, D090).
- **Dependências obrigatórias**: Nenhuma.
- **Dependências proibidas**: Cliente, CT-e, Viagem, Financeiro, Pneu.
- **Dono da Timeline**: Aggregate Provedor de Rastreamento (este próprio).
- **Capacidade Offline**: Consulta Offline.

## Equipamento de Rastreamento

- **Objetivo**: Representa uma unidade de rastreamento/sensoriamento (física ou virtual — ex: o
  próprio app do motorista, no futuro) instalada/vinculada a um Veículo Tracionador. Por D128, um
  Veículo pode ter **múltiplos** Equipamentos simultâneos, cada um com um papel — rastreador
  principal, rastreador backup, câmera, sensor de temperatura (carga frigorífica), TPMS (pressão
  dos pneus), etc.
- **Responsabilidades**: Ligar um Provedor de Rastreamento a um Veículo; ser a origem esperada das
  Posições/Telemetria daquele veículo, qualificada pelo seu `TIPO_EQUIPAMENTO`.
- **O que não faz**: Não decide o significado de negócio de nada que observa (D116); não substitui
  o Veículo Tracionador — é um equipamento acoplado a ele; não exige que todos os papéis existam —
  um veículo pode ter só o rastreador principal, ou também câmera/TPMS, conforme o plano contratado.
- **Aggregate Root**: Sim.
- **Bounded Context proprietário**: `tracking`
- **Principais relacionamentos**: Provedor de Rastreamento (N:1); Veículo Tracionador (referenciado,
  [`003-frota.md`](./003-frota.md), N:1 — múltiplos Equipamentos vigentes por veículo, D128, cada um
  com seu próprio histórico de vínculo, D080).
- **Eventos que publica**: `EquipamentoDeRastreamentoInstalado`, `EquipamentoDeRastreamentoRemovido`
  (novos).
- **Eventos que consome**: Nenhum.
- **Invariantes**: identificador do equipamento (serial/IMEI) único globalmente, não apenas por
  tenant (é um dado físico do equipamento); **no máximo um Equipamento com `TIPO_EQUIPAMENTO =
  Principal` vigente por Veículo** (D128 — os demais papéis podem coexistir em qualquer quantidade,
  inclusive mais de um do mesmo papel, ex: duas câmeras).
- **Regras de negócio associadas**: D001, D005/D006, D080 (vínculo Equipamento × Veículo responde
  Quando começou?/Quando terminou?/Quem alterou?), D084 (identificador do equipamento nunca
  reutilizado), D128 (múltiplos equipamentos simultâneos por veículo, um por papel distinto).
- **Estados**: `Ativo` / `Inativo` / `Removido`.
- **Auditoria**: D007.
- **Linha do tempo**: instalação, remoção, trocas.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Sim, ocorrências de instalação/manutenção do equipamento (D023).
- **KPIs relacionados**: percentual de veículos com equipamento ativo (dado bruto; indicador em
  `analytics`).
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: nenhuma isolada — a evolução prevista no lote anterior
  (múltiplos equipamentos simultâneos) já foi incorporada nesta revisão (D128).
- **Dependências obrigatórias**: Provedor de Rastreamento, Veículo Tracionador.
- **Dependências proibidas**: Cliente, CT-e, Viagem diretamente (é consultado por `freight` via
  evento, nunca o contrário — D008), Financeiro, Pneu.
- **Dono da Timeline**: Aggregate Equipamento de Rastreamento (este próprio) — contribui à do
  Veículo Tracionador por referência.
- **Capacidade Offline**: Consulta Offline.

## Origem de Localização

- **Objetivo**: Catálogo das fontes possíveis de uma posição (GPS do rastreador, App Motorista,
  Triangulação de rede, Manual) — o quinto componente de toda `Posição de Veículo`.
- **Responsabilidades**: Guardar metadados de confiabilidade típica de cada fonte (precisão
  esperada em metros).
- **O que não faz**: Não decide qual fonte usar quando há mais de uma disponível simultaneamente —
  essa é uma regra de infraestrutura/prioridade de fallback, fora do domínio.
- **Aggregate Root**: Sim — entidade de **Referência** (D036).
- **Bounded Context proprietário**: `tracking`
- **Principais relacionamentos**: Posição de Veículo, Leitura de Telemetria (referenciada por
  ambas).
- **Eventos que publica**: Nenhum.
- **Eventos que consome**: Nenhum.
- **Invariantes**: nome único (catálogo compartilhado entre tenants — não carrega dado de negócio
  específico de tenant, é técnico).
- **Regras de negócio associadas**: D046 (candidata a Platform Reference Data — sem `tenant_id`,
  assim como País/Estado; a confirmar quando `010-administracao.md` tratar dados de plataforma).
- **Estados**: Não aplicável.
- **Auditoria**: D007.
- **Linha do tempo**: Não aplicável.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: Nenhuma prevista.
- **Dependências obrigatórias**: Nenhuma.
- **Dependências proibidas**: Cliente, CT-e, Viagem, Financeiro, Pneu.
- **Dono da Timeline**: Não aplicável.
- **Capacidade Offline**: Consulta Offline.

## Posição de Veículo

- **Objetivo**: Uma fotografia no tempo — nunca "o veículo", sempre um instante específico: Veículo
  + Latitude + Longitude + Data/Hora + Fonte.
- **Responsabilidades**: Ser a unidade atômica de localização, de altíssimo volume, consumida por
  `freight` (progresso da viagem), `fleet` (Disponibilidade do Veículo) e `analytics`.
- **O que não faz**: Não decide se a "viagem chegou ao destino" ou qualquer outra interpretação de
  negócio — apenas publica o dado observado (D116); não é editável — cada leitura é um novo
  registro, nunca uma atualização (D123).
- **Aggregate Root**: Sim — entidade **Histórica** por natureza (D037) e **Time Series** (D049/
  D050) desde a concepção, não como reforço posterior.
- **Bounded Context proprietário**: `tracking`
- **Principais relacionamentos**: Veículo Tracionador (referenciado, N:1); Equipamento de
  Rastreamento (referenciado, N:1); Origem de Localização (referenciada, N:1).
- **Eventos que publica**: `PosicaoRegistrada` (novo); `VeiculoEntrouEmGeofence`/
  `VeiculoSaiuDeGeofence` quando a posição cruza uma Cerca Eletrônica (novos, ver `Cerca
  Eletrônica`).
- **Eventos que consome**: Nenhum.
- **Invariantes**: latitude/longitude dentro de faixas válidas; nenhum dos três momentos (captura,
  recebimento, processamento — D125) pode ser posterior ao momento seguinte da cadeia (captura ≤
  recebimento ≤ processamento).
- **Regras de negócio associadas**: D049/D050 (alto volume/Time Series), D074 (granularidade —
  tipicamente milissegundo ou segundo, conforme o Provedor), D116, D123 (imutável), D124/D125
  (captura, recebimento e processamento são três momentos distintos que coexistem — nunca
  colapsados em um único timestamp).
- **Estados**: Não aplicável — é ela própria um registro pontual.
- **Auditoria**: D007 — não no sentido de "quem alterou" (nunca é alterada), mas de origem e
  integridade do dado recebido.
- **Linha do tempo**: consumida pela Timeline do Veículo Tracionador e da Viagem (por referência,
  D022) — não tem timeline própria de negócio (é volume demais para isso; é ela mesma o dado bruto).
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: percentual de cobertura de rastreamento, tempo sem sinal (indicadores em
  `analytics`, D090 — aqui só o dado bruto).
- **Documentos canônicos relacionados**: Nenhum ainda — candidata a `008-RASTREAMENTO.md` em
  `docs/flows/`, ainda não escrito.
- **Evoluções futuras previstas**: predição de ETA por IA a partir da série histórica de posições.
- **Dependências obrigatórias**: Veículo Tracionador, Equipamento de Rastreamento, Origem de
  Localização.
- **Dependências proibidas**: Cliente, CT-e, Financeiro, Pneu, Ordem de Serviço.
- **Dono da Timeline**: Aggregate Veículo Tracionador (via referência — Posição de Veículo não tem
  timeline de negócio própria por ser Time Series de altíssimo volume).
- **Capacidade Offline**: Sim (D039) — o app do motorista pode registrar localmente e sincronizar
  depois, quando ele próprio for a Origem de Localização.

## Leitura de Telemetria

- **Objetivo**: Uma fotografia no tempo dos sinais vitais do veículo — ignição, velocidade, bateria,
  tensão, odômetro, horímetro, RPM, temperatura, combustível, aceleração, frenagem — **nunca
  misturada com `Posição de Veículo`** (que é só localização).
- **Responsabilidades**: Ser a unidade atômica de telemetria, consumida por `fleet` (ex:
  `Leitura de Hodômetro`, `003-frota.md`, quando a origem for telemetria), `maintenance` (RPM/
  temperatura para diagnóstico preditivo, evolução futura) e `analytics`.
- **O que não faz**: Não interpreta os sinais (ex: "motor superaquecendo") — apenas os observa e
  publica (D116); nem todo Provedor/Equipamento envia todos os sinais — campos ausentes são
  `null`, não zero, e isso nunca invalida a leitura como um todo (D126 — qualidade parcial é o
  estado normal esperado, não uma exceção).
- **Aggregate Root**: Sim — entidade **Histórica** (D037) e **Time Series** (D049/D050) desde a
  concepção.
- **Bounded Context proprietário**: `tracking`
- **Principais relacionamentos**: Veículo Tracionador (referenciado, N:1); Equipamento de
  Rastreamento (referenciado, N:1); Posição de Veículo (referenciada, 0..1 — quando o mesmo pacote
  do Provedor trouxe posição e telemetria juntas, sem forçar acoplamento quando não).
- **Eventos que publica**: `TelemetriaRegistrada` (novo); `HodometroAtualizado` (já catalogado —
  quando a leitura de odômetro por telemetria é a origem, consumido por `fleet` conforme já previsto
  em `003-frota.md`).
- **Eventos que consome**: Nenhum.
- **Invariantes**: cada sinal, quando presente, dentro de faixa fisicamente plausível (ex:
  velocidade não-negativa); `data_hora` nunca no futuro.
- **Regras de negócio associadas**: D049/D050, D074 (granularidade), D116.
- **Estados**: Não aplicável.
- **Auditoria**: D007 — origem e integridade do dado recebido.
- **Linha do tempo**: consumida pela Timeline do Veículo Tracionador por referência; sem timeline
  própria (mesmo motivo de `Posição de Veículo`).
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: consumo médio, tempo de motor ligado ocioso (indicadores em `analytics`,
  D090 — aqui só o dado bruto).
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: manutenção preditiva a partir de RPM/temperatura (ver
  [`../product/VISION.md`](../product/VISION.md), capítulo 24) — evolução direta do gatilho por
  quilometragem/tempo já em `Plano de Manutenção Preventiva` ([`004-manutencao.md`](./004-manutencao.md)).
- **Dependências obrigatórias**: Veículo Tracionador, Equipamento de Rastreamento.
- **Dependências proibidas**: Cliente, CT-e, Financeiro, Pneu (referenciado apenas indiretamente via
  `fleet`, nunca lido diretamente daqui), Ordem de Serviço.
- **Dono da Timeline**: Aggregate Veículo Tracionador (via referência).
- **Capacidade Offline**: Sim (D039), mesmo racional de `Posição de Veículo`.

## Heartbeat

- **Objetivo**: Sinal técnico periódico de "equipamento ativo e comunicando" — distinto de uma
  Posição/Telemetria de negócio, análogo ao papel que `Evento Fiscal` cumpre para integrações
  fiscais (D105: evento técnico não é, por si só, dado de negócio).
- **Responsabilidades**: Permitir detectar equipamento silencioso (sem qualquer comunicação, nem
  posição nem telemetria) por tempo além do esperado.
- **O que não faz**: Não carrega posição nem telemetria — só confirma conectividade; não decide
  sozinho que o veículo está "indisponível" (isso é uma regra de `fleet`, consumindo o evento de
  ausência de heartbeat).
- **Aggregate Root**: Sim — entidade **Histórica** (D037), técnica, alto volume.
- **Bounded Context proprietário**: `tracking`
- **Principais relacionamentos**: Equipamento de Rastreamento (referenciado, N:1).
- **Eventos que publica**: `HeartbeatRecebido` (novo); `EquipamentoSilencioso` (novo — quando o
  intervalo esperado é excedido, calculado, não um heartbeat em si).
- **Eventos que consome**: Nenhum.
- **Invariantes**: nunca editado após inserido (D037/D113 — nunca apagado, mesmo redundante).
- **Regras de negócio associadas**: D037, D105 (técnico, não altera domínio diretamente), D111 (a
  chave de idempotência de cada Provedor é declarada na integração — tipicamente o próprio
  identificador de sequência do pacote recebido), D115 (observabilidade da comunicação).
- **Estados**: Não aplicável.
- **Auditoria**: D007.
- **Linha do tempo**: não aparece na timeline de negócio (é técnico) — consultável por
  Suporte/Auditor, mesmo padrão de `Evento Fiscal`.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não aplicável.
- **KPIs relacionados**: uptime por equipamento/fornecedor (indicador em `analytics`, D090).
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: alerta automático de equipamento silencioso além do limite
  configurado.
- **Dependências obrigatórias**: Equipamento de Rastreamento.
- **Dependências proibidas**: Cliente, CT-e, Viagem diretamente, Financeiro, Pneu.
- **Dono da Timeline**: Não aplicável (técnico).
- **Capacidade Offline**: Não.

## Cerca Eletrônica (Geofence)

- **Objetivo**: Representa uma área geográfica de interesse (pátio, cliente, região de risco) usada
  para detectar entrada/saída de um Veículo. Nome de negócio "Cerca Eletrônica"; nome técnico/API
  "Geofence" (D028 — dualidade negócio/UI × código, mesmo princípio de "Cavalo Mecânico"/"Veículo
  Tracionador").
- **Responsabilidades**: Guardar a geometria (círculo com raio, ou polígono) e ser avaliada a cada
  nova `Posição de Veículo` recebida.
- **O que não faz**: Não decide o significado de negócio de uma entrada/saída (D116) — apenas
  publica o evento; a decisão (ex: "chegou ao cliente") é de `freight`.
- **Aggregate Root**: Sim — entidade de **Referência** (D036), mudando pouco após criada.
- **Bounded Context proprietário**: `tracking`
- **Principais relacionamentos**: Cliente/Filial (referenciado, opcional — quando a cerca representa
  um local de negócio conhecido).
- **Eventos que publica**: `CercaEletronicaCadastrada` (novo) — a entrada/saída em si é publicada
  por `Posição de Veículo`, que a avalia.
- **Eventos que consome**: Nenhum.
- **Invariantes**: geometria válida (raio > 0 para círculo; polígono fechado com ao menos 3 pontos).
- **Regras de negócio associadas**: D001, D005/D006, D116.
- **Estados**: `Ativa` / `Inativa`.
- **Auditoria**: D007.
- **Linha do tempo**: cadastro, alterações.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: tempo médio de permanência por cerca (indicador em `analytics`).
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: cercas dinâmicas (acompanhando uma rota planejada, não só um
  ponto fixo).
- **Dependências obrigatórias**: Nenhuma.
- **Dependências proibidas**: CT-e, Financeiro, Pneu, Ordem de Serviço.
- **Dono da Timeline**: Aggregate Cerca Eletrônica (este próprio).
- **Capacidade Offline**: Consulta Offline.

## Evento de Rastreamento

- **Objetivo**: Registra uma ocorrência detectada a partir da série de Posições/Telemetria — Parada,
  Desvio de Rota, Excesso de Velocidade, Entrada/Saída de Cerca Eletrônica, Ignição
  Ligada/Desligada — consolidadas em um `TIPO` (Enum), não uma entidade por tipo (ver Reconciliação
  de nomes acima).
- **Responsabilidades**: Ser o dado de negócio interpretável a partir do fluxo bruto de Posição/
  Telemetria — a ponte entre "dado observado" e "fato relevante", ainda sem decidir a consequência
  (D116 — quem decide a consequência é `freight`/`fleet`/`maintenance`, consumindo o evento);
  classificar sua própria severidade (Informação/Atenção/Alerta/Crítico, D127) para permitir
  priorização automática de notificação sem depender só do `TIPO`.
- **O que não faz**: Não decide a consequência de negócio do que detecta.
- **Aggregate Root**: Sim — entidade **Histórica** (D037), volume moderado (menor que Posição/
  Telemetria, pois é derivada/detectada, não bruta).
- **Bounded Context proprietário**: `tracking`
- **Principais relacionamentos**: Veículo Tracionador (referenciado, N:1); Posição de Veículo
  (referenciada, quando aplicável); Cerca Eletrônica (referenciada, quando `TIPO` é entrada/saída);
  Configuração de Limite de Velocidade (referenciada, quando `TIPO` é excesso de velocidade).
- **Eventos que publica**: `ParadaDetectada`, `DesvioDeRotaDetectado`, `ExcessoDeVelocidadeDetectado`,
  `VeiculoEntrouEmGeofence`, `VeiculoSaiuDeGeofence`, `IgnicaoLigada`, `IgnicaoDesligada` (novos).
- **Eventos que consome**: Nenhum — é ele próprio quem gera os eventos de negócio a partir da
  observação bruta.
- **Invariantes**: todo Evento de Rastreamento tem origem explícita (D099, mesmo princípio aplicado
  aqui: sempre referencia a(s) Posição(ões)/Telemetria que o originaram, D119); toda instância tem
  uma severidade (D127).
- **Regras de negócio associadas**: D017/D018/D037, D116, D119, D127.
- **Estados**: Não aplicável — registro pontual.
- **Auditoria**: D007.
- **Linha do tempo**: consumida pela Timeline do Veículo Tracionador/Viagem por referência (D022).
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Sim, tratativa de exceção (ex: justificativa de desvio de rota,
  D023).
- **KPIs relacionados**: taxa de excesso de velocidade por motorista, tempo parado por viagem
  (indicadores em `analytics`, D090 — aqui só o dado bruto).
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: detecção de novos tipos de evento (ex: colisão, via
  acelerômetro) conforme Provedores oferecerem o dado.
- **Dependências obrigatórias**: Veículo Tracionador.
- **Dependências proibidas**: Cliente diretamente, CT-e, Financeiro, Pneu, Ordem de Serviço.
- **Dono da Timeline**: Aggregate Veículo Tracionador (via referência).
- **Capacidade Offline**: Não (a detecção depende de processamento server-side sobre o fluxo
  recebido).

## Configuração de Limite de Velocidade

- **Objetivo**: Define o limite de velocidade aplicável para detecção de excesso — por via
  (rodovia/perímetro urbano), por Categoria de Veículo, ou um padrão geral do tenant.
- **Responsabilidades**: Ser consultada por `Evento de Rastreamento` ao processar cada nova
  `Posição de Veículo` com velocidade disponível.
- **O que não faz**: Não substitui o limite legal da via — é a referência que o tenant usa até uma
  integração futura com base cartográfica de limites reais.
- **Aggregate Root**: Sim — entidade de **Referência** (D036).
- **Bounded Context proprietário**: `tracking`
- **Principais relacionamentos**: Categoria de Veículo (referenciada, opcional,
  [`003-frota.md`](./003-frota.md)).
- **Eventos que publica**: `ConfiguracaoDeLimiteDeVelocidadeAtualizada` (novo).
- **Eventos que consome**: Nenhum.
- **Invariantes**: limite maior que zero.
- **Regras de negócio associadas**: D001, D005/D006.
- **Estados**: `Ativa` / `Inativa`.
- **Auditoria**: D007.
- **Linha do tempo**: cadastro, alterações.
- **Anexos suportados**: Não aplicável.
- **Comentários suportados**: Não crítico, mas suportado (D023).
- **KPIs relacionados**: Nenhum direto.
- **Documentos canônicos relacionados**: Nenhum ainda.
- **Evoluções futuras previstas**: integração com base cartográfica de limites reais por via.
- **Dependências obrigatórias**: Nenhuma.
- **Dependências proibidas**: Cliente, CT-e, Financeiro, Pneu, Ordem de Serviço.
- **Dono da Timeline**: Aggregate Configuração de Limite de Velocidade (este próprio).
- **Capacidade Offline**: Consulta Offline.
