# 002 — Operação (Viagem e correlatas)

Atributos distintivos das 14 entidades de [`../../domain/002-operacao.md`](../../domain/002-operacao.md).
Atributos universais (`ID`, `CODIGO`, `TENANT_ID`, `VERSAO`, `CRIADO_EM/POR`, `ATUALIZADO_EM/POR`,
`STATUS`) não são repetidos aqui (D069) — ver [`README.md`](./README.md). Tipos Conceituais usados
abaixo seguem exclusivamente o vocabulário padronizado do README (D068).

## Reconciliação de nomes (antes de começar)

A lista de prioridade desta rodada foi dada como "Viagem, Entrega, Ocorrência, Roteiro, Cotação,
Agendamento, Linha de Frete". Três desses nomes não correspondem 1:1 a uma entidade já estabelecida
em `docs/domain/002-operacao.md` — em vez de inventar entidades novas ou ignorar silenciosamente a
diferença (mesmo princípio já aplicado na reconciliação de perfis/personas do RBAC), o mapeamento
fica explícito aqui:

| Nome dado | Entidade real correspondente | Por quê |
|---|---|---|
| Roteiro | **Ponto de Parada da Viagem** | É a entidade que ordena a sequência de paradas planejadas (coleta/entrega/posto/pedágio) de uma Viagem — o que "roteiro" descreve na linguagem de negócio. Não existe uma entidade `Roteiro` própria; "roteirização" (cálculo via Mapbox) é uma capacidade de `routing`, não uma entidade de `freight`. |
| Agendamento | **Atributos da própria Viagem** (`DATA_PROGRAMADA`, `JANELA_PROGRAMADA`) | Não é uma entidade separada — é o resultado da fase "Programação" do fluxo principal (ver [`../../flows/002-VIAGEM.md`](../../flows/002-VIAGEM.md)), que define quando a Viagem sairá de `RASCUNHO` para `PLANEJADA`. Tratado na seção Viagem abaixo. Não confundir com **Janela de Entrega**, que é o intervalo combinado para uma parada específica, não da viagem como um todo. |
| Linha de Frete | **Contrato de Frete** | Termo de mercado para o acordo comercial que baliza condições de fretes futuros — a entidade já catalogada como Contrato de Frete. Conceitualmente combina Cliente + Tabela de Preço/Rota, que é exatamente o papel do Contrato de Frete descrito em `docs/domain/002-operacao.md`. |

As sete entidades priorizadas, portanto, mapeiam para: **Viagem, Entrega, Ocorrência, Ponto de
Parada da Viagem, Cotação, Contrato de Frete** — mais os atributos de programação da própria
Viagem no lugar de "Agendamento". As 8 entidades restantes da categoria (Coleta, Romaneio, Item de
Carga, Canhoto, Item de Cotação, Solicitação de Frete, Janela de Entrega, Alocação de Recurso da
Viagem) são cobertas na sequência, com o mesmo padrão de detalhe usado em `001-cadastros.md`.

---

## Viagem

Dono: `freight` · Natureza: Transactional Data · Fonte canônica do ciclo de vida:
[`../../flows/002-VIAGEM.md`](../../flows/002-VIAGEM.md) (D035).

### Atributos

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| VIAGEM.CLIENTE_ID | Cliente | Referência | Sim | Capturado (sistema, da Solicitação/Cotação aprovada) | Não | Interno | FK para Cliente — dado vivo, não confundir com `CLIENTE_SNAPSHOT` abaixo |
| VIAGEM.MOTORISTA_ID | Motorista atual | Referência | Sim, a partir de `PLANEJADA` | Capturado (sistema) | Sim, via Alocação de Recurso da Viagem | Interno | Dado vivo — aponta para o Motorista vigente; ver `ALOCACAO_RECURSO_VIAGEM` |
| VIAGEM.VEICULO_TRACIONADOR_ID | Veículo Tracionador atual | Referência | Sim, a partir de `PLANEJADA` | Capturado (sistema) | Sim, via Alocação de Recurso da Viagem | Interno | Invariante: exatamente um ativo por vez |
| VIAGEM.DATA_PROGRAMADA | Data programada | Data | Sim, a partir da fase Programação | Informado | Sim (reprogramação gera novo valor auditado) | Interno | Granularidade: dia (D074). Corresponde ao que a lista de prioridade chamou de "Agendamento" — ver Reconciliação acima; não é uma entidade própria |
| VIAGEM.JANELA_PROGRAMADA | Janela de horário programada | Data/Hora | Não | Informado | Sim | Interno | Granularidade: segundo (D074). Não confundir com Janela de Entrega, que é por parada, não da viagem inteira |
| VIAGEM.STATUS_OPERACIONAL | Status Operacional | Enum | Sim | Calculado (transições da máquina de estados) | Sim, em `ViagemStatusHistory` (D017/D018) | Interno | Ver seção de governança abaixo e [`../../flows/002-VIAGEM.md`](../../flows/002-VIAGEM.md) para a máquina completa |
| VIAGEM.STATUS_FISCAL | Status Fiscal | Enum | Sim | Calculado/Capturado (webhook SEFAZ via `documents`) | Sim, em `ViagemStatusHistory` | Interno | Ver seção de governança abaixo |
| VIAGEM.STATUS_FINANCEIRO | Status Financeiro | Enum | Sim | Calculado (eventos de `financial`) | Sim, em `ViagemStatusHistory` | Financeiro | Ver seção de governança abaixo |
| VIAGEM.NOME_MOTORISTA_SNAPSHOT | Nome do motorista (snapshot) | Texto Curto | Sim, a partir da abertura da viagem | Capturado, uma única vez, na abertura da viagem (D071) | Não — é imutável por definição (D073) | Interno | Nunca ressincroniza com `Motorista.NOME` mesmo que o motorista seja renomeado depois (D073/D038) |
| VIAGEM.PLACA_VEICULO_SNAPSHOT | Placa do veículo (snapshot) | Texto Curto | Sim, a partir da abertura da viagem | Capturado, uma única vez, na abertura da viagem (D071) | Não (D073) | Interno | Idem acima, para o Veículo Tracionador |
| VIAGEM.CLIENTE_SNAPSHOT | Dados do cliente (snapshot) | JSON Estruturado | Sim, a partir da abertura da viagem | Capturado, uma única vez, na abertura da viagem (D071) | Não (D073) | LGPD (contém dados de contato) | Razão Social/Nome Fantasia e endereço no momento da viagem — não o Cliente vivo |
| VIAGEM.RECEITA_PREVISTA_SNAPSHOT | Receita Prevista (snapshot) | Monetário | Sim, a partir da Cotação aprovada | Capturado, uma única vez, na aprovação da Cotação (D071) | Financeiro | Moeda: BRL (D075). Fonte canônica do conceito Previsto/Realizado: [`../../flows/005-FINANCEIRO.md`](../../flows/005-FINANCEIRO.md) — aqui só o snapshot, não a apuração |
| VIAGEM.TABELA_PRECO_APLICADA_SNAPSHOT | Tabela de Preço aplicada (snapshot) | Referência | Sim, a partir da Cotação aprovada | Capturado, uma única vez, na aprovação da Cotação (D071) | Não (D073) | Interno | Guarda o ID/versão da Tabela de Preço usada no cálculo — mesmo que a tabela viva seja revisada depois, este valor não muda |
| VIAGEM.CUSTO_PREVISTO | Custo Previsto | Monetário | Não | Calculado (pedágio de referência + estimativa de combustível) | Não (recalculado até `PLANEJADA`; depois congela) | Financeiro | Moeda: BRL (D075). Fonte canônica: `005-FINANCEIRO.md`. **Atributo Crítico (D077)** — par de `CUSTO_REALIZADO`, ver Governança abaixo |
| VIAGEM.CUSTO_REALIZADO | Custo Realizado | Monetário | Não | Derivado — acumulado conforme a viagem executa (soma de Abastecimentos + pedágios + `Item de Ordem de Serviço`/`Rateio de Despesa` rateados, [`006-financeiro.md`](./006-financeiro.md)) | Sim — cada atualização insere novo valor acumulado, nunca sobrescreve o anterior (D018 aplicado a valor monetário) | Financeiro | Moeda: BRL (D075). D098 — nunca substitui `CUSTO_PREVISTO`, os dois coexistem. **Atributo Crítico (D077)** — ver Governança abaixo |
| VIAGEM.MARGEM_PREVISTA | Margem Prevista | Monetário | Não | Calculado (`RECEITA_PREVISTA_SNAPSHOT − CUSTO_PREVISTO`) | Não (recalculada até congelar com `CUSTO_PREVISTO`) | Financeiro | Moeda: BRL (D075). Calculada na Programação, antes da execução — fonte canônica: `005-FINANCEIRO.md` |
| VIAGEM.MARGEM_REALIZADA | Margem Realizada | Monetário | Não | Calculado (`RECEITA_REALIZADA − CUSTO_REALIZADO`) | Sim, junto com `CUSTO_REALIZADO`/`RECEITA_REALIZADA` | Financeiro | Moeda: BRL (D075). Só definitiva quando a Viagem atinge `ENCERRADA` (D019) — antes disso é provisória |
| VIAGEM.DESVIO_FINANCEIRO | Desvio Financeiro | Monetário | Não | Calculado (`MARGEM_REALIZADA − MARGEM_PREVISTA`) | Não | Financeiro | Moeda: BRL (D075). Calculado por instância (esta Viagem), não uma estatística agregada entre viagens — por isso não conflita com D090 (que veda apenas indicadores agregados/estatísticos como EBITDA, resultado por cliente/motorista, esses sim exclusivos de `analytics`) |
| VIAGEM.KM_RODADO | Km rodado | Decimal | Não | Derivado — `leitura_encerramento.valor_km − leitura_despacho.valor_km` (`leituras_hodometro`, `fleet`, [`003-frota.md`](./003-frota.md)) | Não — recalculado a cada leitura de fronteira nova (só duas por Viagem: despacho/encerramento) | Interno | **Reconciliado (V1 Operational Hardening, Parte 2)**: fonte original documentada era "rastreamento/`tracking`" (GPS/telemetria), nunca implementada; hodômetro já é a fonte única e não-duplicada do veículo (D034), com o invariante "nunca decresce" já garantido — mais prático para V1 que depender de hardware de rastreamento. `None`/indisponível quando a Viagem não tiver as duas leituras de fronteira — nunca estimado. Gravado por `TripInternalTransitions.update_km_rodado`, chamado por `TripOdometerRecorder` (`fleet`) — mesmo padrão de `CUSTO_REALIZADO`/`RECEITA_REALIZADA` (derivado de outro módulo, nunca editável direto) |

> **Receita Realizada**: por simetria com `CUSTO_REALIZADO`, existe `VIAGEM.RECEITA_REALIZADA`
> (Monetário, Derivado — soma das `Conta a Receber` da Fatura desta viagem com `STATUS = Recebida`
> ou `Conciliada`, [`006-financeiro.md`](./006-financeiro.md); histórico Sim, mesma lógica de
> acumulação; Financeiro; D098 — nunca substitui `RECEITA_PREVISTA_SNAPSHOT`; **Atributo Crítico
> (D077)**, ver Governança abaixo), apurada quando o Status Financeiro atinge `RECEBIDA`.

### Governança dos atributos críticos — quatro perguntas

Por pedido explícito: todo atributo não-óbvio de Viagem deve responder **Quem altera? / Quando
muda? / Quem pode visualizar? / Quem nunca altera?** — não basta descrever o campo, é preciso
declarar seu ciclo de controle.

| Atributo | Quem altera? | Quando muda? | Quem pode visualizar? | Quem nunca altera? |
|---|---|---|---|---|
| `STATUS_OPERACIONAL` | Fluxo Operacional (Motorista via app, Gestor Operacional para exceções) | A cada transição válida da máquina de estados operacional (ver `002-VIAGEM.md`) | Conforme RBAC (todo perfil com permissão de leitura de Viagem no escopo do tenant) | Frontend (nunca escreve status diretamente — D027); Financeiro/Fiscal (não têm essa permissão) |
| `STATUS_FISCAL` | `documents`, a partir de webhook da SEFAZ (nunca manual) | Emissão/cancelamento de CT-e, emissão/encerramento de MDF-e | Conforme RBAC | Motorista, Gestor Operacional (apenas consultam; quem escreve é o bounded context `documents`) |
| `STATUS_FINANCEIRO` | `financial`, a partir de eventos (Canhoto registrado, cobrança enviada, pagamento confirmado) | Faturamento, envio de cobrança, confirmação de recebimento | Conforme RBAC (Financeiro sempre; demais perfis conforme escopo) | Motorista, Gestor Operacional, Fiscal (apenas consultam) |
| `ENCERRADA` (status composto) | **Ninguém** — nunca é setado diretamente por nenhum perfil, nem Administrador SaaS (D019) | Automaticamente, quando as três dimensões acima convergem para seus estados terminais | Conforme RBAC | Todos — é sempre calculado, nunca persistido como campo editável (D072); correções excepcionais são baixa financeira em `005-FINANCEIRO.md`, nunca uma transição forçada |
| `NOME_MOTORISTA_SNAPSHOT` | Motorista (indiretamente — o valor é copiado do cadastro do Motorista no momento da abertura da viagem) | Uma única vez, na abertura da viagem | Conforme RBAC | O próprio processo depois da captura — nunca reatualiza mesmo que `Motorista.NOME` mude (preserva histórico, D073) |
| `PLACA_VEICULO_SNAPSHOT` | Veículo Tracionador (indiretamente, na abertura da viagem) | Uma única vez, na abertura da viagem | Conforme RBAC | O próprio processo depois da captura (D073) |
| `CLIENTE_SNAPSHOT` | Cliente (indiretamente, na abertura da viagem) | Uma única vez, na abertura da viagem | Conforme RBAC + regras de LGPD (dado classificado) | O próprio processo depois da captura (D073) |
| `RECEITA_PREVISTA_SNAPSHOT` | Cotação (indiretamente — copiado no momento da aprovação) | Uma única vez, na aprovação da Cotação que originou a viagem | Financeiro sempre; demais perfis conforme RBAC (dado sensível financeiramente) | O próprio processo depois da captura — mesmo que a Tabela de Preço seja revisada depois (D073) |
| `TABELA_PRECO_APLICADA_SNAPSHOT` | Cotação (indiretamente, na aprovação) | Uma única vez, na aprovação da Cotação | Conforme RBAC | O próprio processo depois da captura (D073) |
| `CUSTO_REALIZADO` | `financial`, indiretamente — via eventos de Abastecimento/pedágio/Ordem de Serviço rateada (nunca editado à mão) | A cada novo custo incorrido, do início da execução até `ENCERRADA` | Financeiro sempre; demais perfis conforme RBAC | Motorista, Gestor Operacional (apenas consultam); Frontend (D027) |
| `RECEITA_REALIZADA` | `financial`, indiretamente — via confirmação de recebimento de `Conta a Receber` ([`006-financeiro.md`](./006-financeiro.md)) | Quando o Status Financeiro atinge `RECEBIDA` | Financeiro sempre; demais perfis conforme RBAC (dado sensível financeiramente) | Todos os demais perfis; Frontend (D027) |

---

## Entrega

Dono: `freight` · Natureza: Transactional Data · Parte do agregado Viagem.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| ENTREGA.VIAGEM_ID | Viagem | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| ENTREGA.ORDEM | Ordem da parada | Inteiro | Sim | Informado (na Programação) | Não | Interno | Sequência dentro da mesma Viagem, análoga à de Ponto de Parada da Viagem |
| ENTREGA.DESTINATARIO | Destinatário | Texto Curto | Sim | Informado | Não | LGPD (quando pessoa física) | |
| ENTREGA.ENDERECO_ENTREGA | Endereço de entrega | JSON Estruturado | Sim | Informado | Não | Interno | Value Object Endereço |
| ENTREGA.STATUS | Status da Entrega | Enum | Sim | Calculado/Informado (registro de campo) | Sim | Interno | Valores: `Pendente`/`Concluída`/`Recusada`/`Devolvida`/`Cancelada` — Quem altera: Motorista (app), exceção via Gestor Operacional; Quando muda: registro de campo na parada; Quem visualiza: conforme RBAC; Quem nunca altera: Frontend sozinho (regra crítica vive no backend, D027) |
| ENTREGA.DATA_HORA_CONCLUSAO | Data/hora de conclusão | Data/Hora | Não | Capturado (app motorista) | Não | Interno | Granularidade: segundo (D074) |
| ENTREGA.MOTIVO_RECUSA | Motivo da recusa | Texto Longo | Não, obrigatório quando `Recusada` | Informado | Não | Interno | Alimenta a decisão de Devolução vs. Reentrega |

## Coleta

Dono: `freight` · Natureza: Transactional Data (marco pontual, sem ciclo de vida próprio).

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| COLETA.VIAGEM_ID | Viagem | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| COLETA.DATA_HORA | Data/hora da coleta | Data/Hora | Sim | Capturado (sistema) | Não | Interno | Granularidade: segundo (D074) |
| COLETA.LOCAL | Local da coleta | Localização | Não | Capturado (GPS do app) | Não | Interno | Latitude/Longitude no momento do registro — coluna física existe, ainda não populada (Reconciliado abaixo) |
| COLETA.CONFERENCIA_OK | Carga conferida | Booleano | Sim | Informado | Não | Interno | Informativa — o gatilho de `EM_DESLOCAMENTO → CARREGANDO` é a própria criação da Coleta, não o valor deste campo (correção desta reconciliação: a nota anterior citava `CARREGANDO → EM_TRANSITO`, que na verdade depende do Romaneio, não da Coleta) |

**Reconciliado (V1 Operational Hardening, Parte 2)**: `POST /viagens/{id}/coletas`
(`018-trip-status.md`) implementa exatamente este contrato — `DATA_HORA` é sempre o instante do
comando (`Capturado (sistema)`, não mais "app motorista" nesta rodada, que expõe só a web do
Gestor); `LOCAL` (Geography) existe na tabela física mas segue sem captura de geolocalização —
gap documentado, não implementado (depende de o app do Motorista existir e pedir permissão de
GPS, fora de escopo desta rodada; `freight.pickup.create` já reserva `App: ●` no `RBAC_MATRIX`
para quando isso acontecer).

## Ocorrência

Dono: `freight` · Natureza: Transactional Data · Parte do agregado Viagem.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| OCORRENCIA.VIAGEM_ID | Viagem | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| OCORRENCIA.TIPO | Tipo | Enum | Sim | Informado | Não | Interno | Valores: Atraso/Avaria/Pane/Sinistro/Outro |
| OCORRENCIA.DESCRICAO | Descrição | Texto Longo | Sim | Informado | Não | Interno | |
| OCORRENCIA.STATUS | Status | Enum | Sim | Informado | Sim | Interno | Valores: `Aberta`/`Resolvida` — Quem altera: quem registrou ou Gestor Operacional; Quando muda: ao tratar a ocorrência; Quem visualiza: conforme RBAC; Quem nunca altera: a Ocorrência não decide sozinha a transição da Viagem para `INTERROMPIDA` — essa é uma decisão do Gestor Operacional, apenas informada pela Ocorrência |
| OCORRENCIA.DATA_HORA | Data/hora do registro | Data/Hora | Sim | Capturado (sistema) | Não | Interno | Granularidade: segundo (D074) |
| OCORRENCIA.GRAVIDADE | Gravidade | Enum | Não | Informado | Não | Interno | Valores: Baixa/Média/Alta/Crítica — informa, mas não decide sozinha a interrupção da viagem |

## Romaneio

Dono: `freight` · Natureza: Transactional Data · Parte do agregado Viagem.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| ROMANEIO.VIAGEM_ID | Viagem | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| ROMANEIO.NUMERO_DOCUMENTO | Número do romaneio | Texto Curto | Não | Informado/Importado | Não | Interno | Não substitui o CT-e — ver [`../../flows/009-FISCAL.md`](../../flows/009-FISCAL.md) |

**Reconciliado (V1 Operational Hardening, Parte 2/3)**: `POST /viagens/{id}/romaneios`
(`018-trip-status.md`) implementa este contrato — confirmação do Romaneio (com ao menos um Item de
Carga, invariante reforçada na criação) é o gatilho real de `CARREGANDO → EM_TRANSITO`/`EM_ENTREGA`.

## Item de Carga

Dono: `freight` · Natureza: Transactional Data · Parte do agregado Viagem (via Romaneio).

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| ITEM_CARGA.ROMANEIO_ID | Romaneio | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| ITEM_CARGA.DESCRICAO | Descrição | Texto Curto | Sim | Informado | Não | Interno | |
| ITEM_CARGA.PESO | Peso | Decimal | Sim | Informado | Não | Interno | Maior que zero |
| ITEM_CARGA.QUANTIDADE | Quantidade | Inteiro | Sim | Informado | Não | Interno | Maior que zero |

## Canhoto

Dono: `freight` · Natureza: Transactional Data · Parte do agregado Viagem (via Entrega).

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| CANHOTO.ENTREGA_ID | Entrega | Referência | Sim | Capturado (sistema) | Não | Interno | FK 1:1, imutável |
| CANHOTO.STATUS | Status | Enum | Sim | Informado | Sim | Interno | Valores: `Pendente`/`Registrado` — Quem altera: Motorista (app); Quando muda: no momento da entrega; Quem visualiza: conforme RBAC + Financeiro sempre (gatilho de faturamento); Quem nunca altera: `financial` só lê, nunca escreve o Canhoto |
| CANHOTO.DATA_HORA_REGISTRO | Data/hora do registro | Data/Hora | Não | Capturado (app motorista) | Não | Interno | Granularidade: segundo (D074) |
| CANHOTO.ASSINATURA_ARQUIVO_ID | Assinatura/foto | Arquivo | Não | Capturado (app motorista) | Não | LGPD | Anexo — D024 |

## Contrato de Frete

Dono: `freight` · Natureza: Master Data · Aggregate Root · ("Linha de Frete" na reconciliação acima).

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| CONTRATO_FRETE.CLIENTE_ID | Cliente | Referência | Sim | Informado | Não | Interno | FK |
| CONTRATO_FRETE.TABELA_PRECO_ID | Tabela de Preço referenciada | Referência | Não | Informado | Não | Interno | Não substitui a Tabela — apenas a referencia |
| CONTRATO_FRETE.VIGENCIA_INICIO | Início da vigência | Data | Sim | Informado | Não | Interno | Granularidade: dia (D074) |
| CONTRATO_FRETE.VIGENCIA_FIM | Fim da vigência | Data | Não | Informado | Não | Interno | Granularidade: dia (D074); deve ser posterior ao início |
| CONTRATO_FRETE.STATUS | Status | Enum | Sim | Informado/Calculado | Sim | Interno | Valores: `Ativo`/`Encerrado` |
| CONTRATO_FRETE.SLA_ACORDADO | SLA acordado | Texto Longo | Não | Informado | Não | Interno | Condições de prazo negociadas — referenciadas, não recalculadas aqui |

## Cotação

Dono: `freight` · Natureza: Transactional Data · Aggregate Root até aprovação.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| COTACAO.CLIENTE_ID | Cliente | Referência | Sim | Capturado (sistema) | Não | Interno | FK |
| COTACAO.CONTRATO_FRETE_ID | Contrato de Frete referenciado | Referência | Não | Informado | Não | Interno | Opcional — quando a cotação nasce de um contrato guarda-chuva |
| COTACAO.VALOR_TOTAL | Valor total | Monetário | Sim | Calculado (soma dos Itens de Cotação) | Sim (revisões antes da aprovação, D017/D018) | Financeiro | Moeda: BRL (D075); maior que zero |
| COTACAO.STATUS | Status | Enum | Sim | Informado/Calculado | Sim | Interno | Valores: `Rascunho`/`Aprovada`/`Recusada`/`Expirada` — Quem altera: Comercial/Cliente (Portal, fases futuras); Quando muda: negociação e decisão do cliente; Quem visualiza: conforme RBAC; Quem nunca altera: uma Cotação `Aprovada` nunca é editada — gera uma nova Cotação |
| COTACAO.DATA_VALIDADE | Validade da proposta | Data | Sim | Informado | Não | Interno | Granularidade: dia (D074); gatilho de transição automática para `Expirada` |

## Item de Cotação

Dono: `freight` · Natureza: Transactional Data · Parte do agregado Cotação.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| ITEM_COTACAO.COTACAO_ID | Cotação | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| ITEM_COTACAO.DESCRICAO | Descrição (frete/pedágio/taxa) | Texto Curto | Sim | Informado | Não | Interno | |
| ITEM_COTACAO.VALOR | Valor | Monetário | Sim | Informado/Calculado | Não | Financeiro | Moeda: BRL (D075); maior ou igual a zero |

## Solicitação de Frete

Dono: `freight` · Natureza: Transactional Data · Aggregate Root até originar Cotação.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| SOLICITACAO_FRETE.CLIENTE_ID | Cliente | Referência | Sim | Informado | Não | Interno | FK |
| SOLICITACAO_FRETE.ORIGEM | Origem | JSON Estruturado | Sim | Informado | Não | Interno | Endereço/local de coleta |
| SOLICITACAO_FRETE.DESTINOS | Destino(s) | JSON Estruturado | Sim | Informado | Não | Interno | Um ou mais endereços — suporta multi-drop desde a solicitação |
| SOLICITACAO_FRETE.TIPO_CARGA | Tipo de carga | Enum | Sim | Informado | Não | Interno | |
| SOLICITACAO_FRETE.PRAZO_DESEJADO | Prazo desejado | Data | Não | Informado | Não | Interno | Granularidade: dia (D074) — desejo do cliente, não compromisso |
| SOLICITACAO_FRETE.STATUS | Status | Enum | Sim | Informado/Calculado | Sim | Interno | Valores: `Registrada`/`Cotada`/`Descartada` |

## Janela de Entrega

Dono: `freight` · Natureza: Transactional Data · Parte do agregado Viagem (via Entrega).

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| JANELA_ENTREGA.ENTREGA_ID | Entrega | Referência | Sim | Capturado (sistema) | Não | Interno | FK 1:1, imutável |
| JANELA_ENTREGA.HORA_INICIO | Hora inicial | Data/Hora | Sim | Informado | Não | Interno | Granularidade: segundo (D074) |
| JANELA_ENTREGA.HORA_FIM | Hora final | Data/Hora | Sim | Informado | Não | Interno | Granularidade: segundo (D074); deve ser posterior à hora inicial |

## Ponto de Parada da Viagem

Dono: `freight` · Natureza: Transactional Data · Parte do agregado Viagem · ("Roteiro" na
reconciliação acima).

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| PONTO_PARADA_VIAGEM.VIAGEM_ID | Viagem | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| PONTO_PARADA_VIAGEM.TIPO | Tipo de parada | Enum | Sim | Informado/Calculado (roteirização) | Não | Interno | Valores: Coleta/Entrega/Posto/Pedágio |
| PONTO_PARADA_VIAGEM.ORDEM | Ordem na sequência | Inteiro | Sim | Informado/Calculado (roteirização via Mapbox) | Não | Interno | Única dentro da mesma Viagem — este é o campo que "roteiro" descreve na linguagem de negócio |
| PONTO_PARADA_VIAGEM.LOCALIZACAO | Localização planejada | Localização | Sim | Informado | Não | Interno | Latitude/Longitude — planejamento, não é a posição em tempo real (essa é `tracking`) |
| PONTO_PARADA_VIAGEM.STATUS | Status | Enum | Sim | Informado/Calculado | Não | Interno | Valores: `Planejado`/`Concluído` |

## Alocação de Recurso da Viagem

Dono: `freight` · Natureza: Transactional Data · Parte do agregado Viagem.

| Atributo | Nome | Tipo Conceitual | Obrigatório | Origem | Histórico | Classificação | Observações |
|---|---|---|---|---|---|---|---|
| ALOCACAO_RECURSO_VIAGEM.VIAGEM_ID | Viagem | Referência | Sim | Capturado (sistema) | Não | Interno | FK, imutável |
| ALOCACAO_RECURSO_VIAGEM.MOTORISTA_ID | Motorista | Referência | Sim | Informado (Gestor Operacional) | Sim (append-only, D017/D018) | Interno | Nunca sobrescrito — reatribuição gera novo registro |
| ALOCACAO_RECURSO_VIAGEM.VEICULO_TRACIONADOR_ID | Veículo Tracionador | Referência | Sim | Informado | Sim | Interno | Idem acima |
| ALOCACAO_RECURSO_VIAGEM.IMPLEMENTO_ID | Implemento | Referência | Não | Informado | Sim | Interno | Idem acima |
| ALOCACAO_RECURSO_VIAGEM.STATUS | Status | Enum | Sim | Calculado | Sim | Interno | Valores: `Vigente`/`Substituída`/`Encerrada` (Reconciliado, V1 Operational Hardening Parte 1) — invariante: no máximo uma `Vigente` por Viagem em cada instante. `Substituída` = trocada por outra na mesma Viagem ainda ativa; `Encerrada` = a Viagem dona terminou (Finalizada/Cancelada) |
| ALOCACAO_RECURSO_VIAGEM.MOTIVO_TROCA | Motivo da troca | Texto Longo | Não, obrigatório quando substitui uma alocação anterior | Informado | Não | Interno | Registrado como comentário na Timeline (D023) |

## Como este documento cresce

Mesmo princípio de todo o dicionário: um arquivo `NNN-categoria.md` por vez, na ordem do roadmap
(ver [`README.md`](./README.md)). Próximo: `003-frota.md`.
