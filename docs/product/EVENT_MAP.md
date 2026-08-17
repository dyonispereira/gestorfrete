# EVENT_MAP.md — Mapa de Eventos de Domínio

Este é o catálogo de Domain Events do GestorFrete: o que dispara cada evento, quem publica e quem
consome. Quando a integração com RabbitMQ for implementada (ver
[`../architecture/event-driven.md`](../architecture/event-driven.md) e
`core/messaging/rabbitmq_client.py`), este documento se torna quase diretamente a lista de
exchanges/routing keys e de consumers a implementar — por isso ele precisa ser preciso, não
apenas ilustrativo.

**Convenção de nomenclatura** (registrada em [`DECISIONS.md`](./DECISIONS.md), D013): o nome do
evento é a linguagem ubíqua do negócio — português, no passado, PascalCase (`ViagemCriada`, não
`TripCreated` nem `trip.created`). Quem publica/consome é identificado pelo nome técnico do bounded
context (`freight`, `financial`, etc. — ver [`../architecture/ddd.md`](../architecture/ddd.md)),
que é o nome real da pasta em `apps/api/src/modules/`.

## Exemplo de leitura da tabela

```
Nova viagem criada
  ↓ gera evento ↓
ViagemCriada
  ↓ consumido por ↓
financial · tracking · mobile · analytics · notification_center · audit
```

---

## Eventos publicados por `freight` (Operação)

| Evento | Gerado quando | Consumido por |
|---|---|---|
| `ViagemCriada` | Uma viagem é criada e associada a motorista, veículo e cliente. | `financial`, `tracking`, `mobile`, `analytics`, `notification_center`, `audit` |
| `MotoristaAceitouViagem` | O motorista aceita, no app, uma Viagem já atribuída a ele — nunca muda o Status Operacional, a Viagem permanece `PLANEJADA` (D129). | `mobile`, `notification_center`, `audit` |
| `ViagemDespachada` | O gestor operacional confirma o despacho da viagem. | `documents` (dispara emissão de CT-e), `tracking`, `mobile`, `notification_center` |
| `ColetaRealizada` | O motorista registra a coleta da carga na origem. | `documents` (romaneio), `notification_center`, `audit` |
| `EntregaRealizada` | O motorista registra a entrega e o canhoto. | `documents` (fecha o canhoto), `financial` (libera faturamento), `notification_center`, `audit` |
| `OcorrenciaRegistrada` | Um imprevisto é registrado durante a viagem (atraso, avaria, etc.). | `notification_center`, `support`, `analytics`, `audit` |
| `ViagemReatribuida` | O gestor troca o motorista/veículo de uma viagem em andamento. | `financial`, `tracking`, `mobile`, `notification_center`, `audit` |
| `ViagemConcluida` | A viagem é encerrada após entrega confirmada. | `financial`, `analytics`, `audit` |
| `ViagemInterrompida` | A viagem entra em pane, sinistro ou ocorrência grave em rota. | `maintenance` (pane), `notification_center`, `support`, `audit` |
| `ViagemCancelada` | A viagem é cancelada, antes ou durante a execução. | `financial` (estorna cobrança pendente, se houver), `notification_center`, `audit` |
| `EntregaRecusada` | O destinatário recusa a carga (total ou parcial) em uma parada. | `financial`, `notification_center`, `audit` |
| `ReentregaAgendada` | Uma nova tentativa é agendada para uma entrega não concluída. | `mobile`, `notification_center`, `audit` |
| `AvariaRegistrada` | Dano é identificado na carga durante conferência. | `notification_center`, `support`, `audit` |
| `ViagemEncerrada` | O Status Composto da viagem atinge `ENCERRADA` — Operacional, Fiscal e Financeiro convergiram (D019/D020). | `analytics`, `audit`, `notification_center` |
| `AbastecimentoSolicitado` | Motorista solicita autorização de abastecimento. | `notification_center`, `audit` |
| `AbastecimentoAutorizado` | Autorização de abastecimento concedida. | `mobile`, `audit` |
| `AbastecimentoRegistrado` | Abastecimento executado no posto, cupom/hodômetro/litros registrados. | `financial` (Custo Realizado — ver [`../flows/005-FINANCEIRO.md`](../flows/005-FINANCEIRO.md)), `analytics`, `audit` |
| `AbastecimentoValidado` | Média de consumo confirmada dentro do esperado. | `analytics`, `audit` |
| `AbastecimentoSuspeito` | Média fora do esperado ou inconsistência detectada. | `notification_center`, `support`, `audit` |
| `AbastecimentoRejeitado` | Investigação confirma fraude/erro; não entra no Custo Realizado. | `financial`, `audit` |
| `CanhotoRegistrado` | O comprovante de entrega (Canhoto) é confirmado, físico ou digital. | `financial` (gatilho de faturamento — ver [`../flows/005-FINANCEIRO.md`](../flows/005-FINANCEIRO.md)), `notification_center`, `audit` |

*(Detalhamento completo do ciclo de vida da Viagem, incluindo as três dimensões de status e o
histórico de transições que geram estes eventos, em [`../flows/002-VIAGEM.md`](../flows/002-VIAGEM.md);
detalhamento do Abastecimento em [`../flows/006-ABASTECIMENTO.md`](../flows/006-ABASTECIMENTO.md).)*

## Eventos publicados por `documents` (Documentos Fiscais)

*(`CanhotoRegistrado` foi movido para a seção `freight` — o Canhoto é parte do agregado Viagem, não
um documento fiscal formal como CT-e/MDF-e; ver D033/D034 e
[`../domain/002-operacao.md`](../domain/002-operacao.md).)*

| Evento | Gerado quando | Consumido por |
|---|---|---|
| `CTeEmitido` | Um CT-e é emitido com sucesso na SEFAZ para uma viagem. | `financial` (habilita faturamento), `analytics`, `audit` |
| `CTeCancelado` | Um CT-e emitido é cancelado. | `financial` (estorna faturamento pendente), `audit` |
| `MDFeEmitido` | Um MDF-e consolidando um ou mais CT-e é emitido. | `analytics`, `audit` |
| `MDFeEncerrado` | O MDF-e é encerrado na SEFAZ ao concluir a última entrega da viagem. | `freight` (avança o Status Fiscal para `MDFE_ENCERRADO`), `analytics`, `audit` |
| `CTeDenegado` | A SEFAZ rejeita a emissão do CT-e (ex: CNPJ irregular). | `freight` (impede `ViagemDespachada` de prosseguir), `notification_center`, `audit` |
| `CTeCorrigido` | Uma Carta de Correção é anexada a um CT-e `AUTORIZADO`. | `analytics`, `audit` |
| `MDFeCancelado` | Um MDF-e é cancelado antes do encerramento. | `financial`, `audit` |
| `CIOTRegistrado` | O CIOT de uma viagem com motorista autônomo é registrado junto à ANTT. | `analytics`, `audit` |
| `CIOTCancelado` | Um CIOT é cancelado antes do início da viagem. | `audit` |

*(Detalhamento completo do ciclo fiscal — CT-e, MDF-e, CIOT, cancelamentos e carta de correção —
em [`../flows/009-FISCAL.md`](../flows/009-FISCAL.md).)*

## Eventos publicados por `financial` (Financeiro)

| Evento | Gerado quando | Consumido por |
|---|---|---|
| `FaturamentoGerado` | Uma cobrança de frete é gerada a partir de CT-e + Canhoto. | `analytics`, `audit`, `notification_center` |
| `AdiantamentoConcedido` | Um adiantamento é registrado para um motorista. | `drivers` (reflete no app do motorista via `mobile`), `notification_center`, `audit` |
| `HaverApurado` | O haver de um motorista é calculado ao final de um ciclo. | `drivers`, `mobile`, `notification_center`, `audit` |
| `ContaAPagarRegistrada` | Uma despesa (peça, combustível, serviço) é lançada. | `analytics`, `audit` |
| `ContaAReceberRegistrada` | Um valor a receber de cliente é lançado. | `analytics`, `audit` |
| `RecebimentoConfirmado` | O pagamento do cliente referente a uma viagem é confirmado. | `freight` (avança o Status Financeiro para `RECEBIDA`), `analytics`, `audit` |
| `ContaAPagarAprovada` | Uma despesa acima da alçada é aprovada. | `audit` |
| `ContaAPagarRejeitada` | Uma despesa acima da alçada é rejeitada. | `notification_center`, `audit` |
| `ContaAPagarConciliada` | Um pagamento é conferido contra o extrato bancário. | `analytics`, `audit` |
| `EstornoRealizado` | Uma Fatura, Conta a Pagar ou Conta a Receber é corrigida por estorno, preservando o histórico original. | `analytics`, `audit`, `notification_center` |
| `CustoRealizadoAtualizado` | Um novo custo é acumulado ao Custo Realizado de uma viagem. | `freight`, `analytics`, `audit` |
| `MargemCalculada` | A Margem Prevista ou Realizada de uma viagem é (re)calculada. | `analytics`, `audit` |

*(Detalhamento completo, incluindo a separação Previsto vs. Realizado e as máquinas de Faturamento
e Contas a Pagar, em [`../flows/005-FINANCEIRO.md`](../flows/005-FINANCEIRO.md).)*

## Eventos publicados por `fleet` (Frota)

| Evento | Gerado quando | Consumido por |
|---|---|---|
| `VeiculoCadastrado` | Um Veículo Tracionador é criado. | `audit` |
| `VeiculoInativado` | Um Veículo Tracionador é desativado (soft delete). | `audit` |
| `ImplementoCadastrado` | Um Implemento é criado. | `audit` |
| `CategoriaDeVeiculoCadastrada` | Uma Categoria de Veículo é criada. | `audit` |
| `ComposicaoVeicularValidada` | `POST /vehicle-compositions/{id}/commands/validate` marca a composição `VALIDA`/`INVALIDA`. | `audit`, `notification_center` (se `INVALIDA`) |
| `HodometroAtualizado` | Uma nova Leitura de Hodômetro é registrada. | `audit` |
| `DocumentoDoVeiculoProximoDoVencimento` | A validade de um Documento do Veículo se aproxima. | `notification_center`, `audit` |

D366 — seção adicionada ao preparar o Sprint 11 Lote 4 (Backend): `domain/003-frota.md` já nomeava
estes eventos como "novos" desde o Sprint 09, nunca catalogados aqui. `ApoliceProximaDoVencimento`/
`LicenciamentoRegistrado`/`LicenciamentoProximoDoVencimento` (Seguro/Licenciamento) ficam de fora —
essas entidades não são implementadas no Lote 4 (D362).

## Eventos publicados por `maintenance` (Frota e Manutenção)

| Evento | Gerado quando | Consumido por |
|---|---|---|
| `OrdemServicoAberta` | Uma ordem de serviço é criada para um veículo. | `fleet` (marca veículo em manutenção), `notification_center`, `audit` |
| `OrdemServicoAprovacaoPendente` | O custo estimado de uma OS excede a alçada do Mecânico/Analista de Frota. | `notification_center`, `audit` |
| `OrdemServicoAprovada` | O Gestor/Analista de Frota aprova o custo de uma OS acima da alçada. | `notification_center`, `audit` |
| `OrdemServicoReprovada` | O Gestor/Analista de Frota reprova o custo de uma OS acima da alçada. | `notification_center`, `audit` |
| `PecaSolicitada` | Uma OS precisa de peça não disponível em estoque. | `notification_center`, `audit` |
| `OrdemServicoConcluida` | O mecânico encerra a execução da ordem de serviço. | `fleet` (libera veículo), `analytics`, `audit` |
| `OrdemServicoFechada` | Os custos da OS são consolidados e lançados no Centro de Custo. | `financial` (custo em centro de custo), `analytics`, `audit` |
| `OrdemServicoCancelada` | Uma OS é cancelada antes do início da execução. | `notification_center`, `audit` |
| `PneuCadastrado` | Um pneu é recebido e recebe sua Marca de Fogo. | `analytics`, `audit` |
| `PneuInstalado` | Um pneu é montado em um veículo/posição. | `fleet`, `analytics`, `audit` |
| `PneuEnviadoParaRecapagem` | Um pneu desgastado é enviado à recapadora. | `analytics`, `audit` |
| `PneuSucateado` | Um pneu chega ao fim da vida útil. | `financial` (baixa de ativo), `analytics`, `audit` |
| `PneuBaixado` | A baixa contábil de um pneu sucateado é confirmada. | `financial`, `analytics`, `audit` |
| `ChecklistIniciado` | O preenchimento de um checklist começa. | `audit` |
| `ChecklistConcluido` | Todos os itens de um checklist são respondidos. | `audit` |
| `ChecklistAprovado` | Um checklist é aprovado (nenhum item crítico reprovado). | `freight` (libera `AGUARDANDO_CHECKLIST → LIBERADA`), `notification_center`, `audit` |
| `ChecklistReprovado` | Um checklist reprova (item crítico reprovado). | `freight` (bloqueia despacho do veículo), `notification_center`, `audit` |

*(Detalhamento completo dos ciclos de OS, Pneu e Checklist em
[`../flows/003-MANUTENCAO.md`](../flows/003-MANUTENCAO.md),
[`../flows/004-PNEUS.md`](../flows/004-PNEUS.md) e
[`../flows/007-CHECKLIST.md`](../flows/007-CHECKLIST.md).)*

## Eventos publicados por `tracking` (Rastreamento)

| Evento | Gerado quando | Consumido por |
|---|---|---|
| `PosicaoRegistrada` | Uma nova posição de veículo é capturada, de qualquer origem. | `freight`, `analytics` |
| `HeartbeatRecebido` | Sinal periódico de atividade recebido de uma origem de rastreamento. | `audit` |
| `PerdaDeSinalDetectada` | Heartbeat ausente além do limite configurado. | `notification_center`, `audit` |
| `GeofenceEntrada` / `GeofenceSaida` | Veículo cruza uma cerca virtual cadastrada. | `notification_center`, `analytics`, `audit` |
| `ParadaIniciada` / `ParadaEncerrada` | Início/fim de um intervalo sem deslocamento acima do limite. | `analytics`, `audit` |
| `DesvioDeRotaDetectado` | Posição fora do corredor da rota planejada. | `notification_center`, `analytics`, `audit` |
| `VelocidadeExcedidaDetectada` | Velocidade acima do limite configurado. | `notification_center`, `mobile` (Meu Desempenho), `analytics`, `audit` |

*(Detalhamento completo, incluindo as múltiplas origens de localização e seus níveis de
confiabilidade, em [`../flows/008-RASTREAMENTO.md`](../flows/008-RASTREAMENTO.md).)*

## Eventos publicados por `mobile` (App Motorista)

| Evento | Gerado quando | Consumido por |
|---|---|---|
| `ViagemBaixadaOffline` | O motorista baixa uma viagem para uso offline. | `audit` |
| `FotoCapturada` | Uma foto é registrada localmente no app. | `audit` |
| `FotoSincronizada` | O upload de uma foto é concluído. | `documents`, `audit` |
| `AssinaturaColetada` | A assinatura digital do destinatário é capturada. | `documents`, `audit` |
| `OCRProcessado` | A leitura automática de um documento fotografado é concluída. | `audit` |
| `SincronizacaoConcluida` | Todos os dados pendentes de um dispositivo são enviados com sucesso. | `analytics`, `audit` |
| `SincronizacaoFalhou` | Uma tentativa de sincronização não é concluída. | `notification_center`, `audit` |

*(Detalhamento completo, incluindo o módulo Meu Desempenho, em
[`../flows/010-APP_MOTORISTA.md`](../flows/010-APP_MOTORISTA.md).)*

## Eventos publicados por `drivers` (Motoristas)

| Evento | Gerado quando | Consumido por |
|---|---|---|
| `HabilitacaoProximaDoVencimento` | A CNH de um motorista está próxima do vencimento (regra de data, sem IA). | `notification_center`, `audit` |

## Eventos publicados por `billing` / `subscription` (Billing e Assinatura)

| Evento | Gerado quando | Consumido por |
|---|---|---|
| `AssinaturaCriada` | Um novo tenant conclui o onboarding e ativa um plano. | `analytics`, `audit`, `notification_center` |
| `PlanoAlterado` | Um tenant faz upgrade/downgrade de plano. | `analytics`, `audit` |
| `CobrancaRealizada` | A cobrança recorrente do tenant é processada com sucesso. | `analytics`, `audit`, `notification_center` |
| `CobrancaFalhou` | A cobrança recorrente falha. | `notification_center` (alerta o tenant), `support`, `audit` |
| `AssinaturaCancelada` | O tenant solicita cancelamento ou o cancelamento é efetivado ao fim do ciclo pago. | `tenancy` (agenda a suspensão do acesso), `analytics`, `audit`, `notification_center` |

## Eventos publicados por `tenancy` (Tenant)

| Evento | Gerado quando | Consumido por |
|---|---|---|
| `TenantProvisionado` | Um novo tenant é criado ao final do fluxo de onboarding. | `identity_access` (cria o Usuário Master), `analytics`, `audit`, `notification_center` |
| `TenantSuspenso` | O tenant transita para `SUSPENSO` (trial expirado ou inadimplência não regularizada). | `identity_access` (bloqueia login), `notification_center`, `audit` |
| `TenantReativado` | O tenant volta de `SUSPENSO`/`CANCELADO` para `ATIVO`. | `identity_access`, `notification_center`, `audit` |

*(Detalhamento completo, incluindo a máquina de estados de Tenant/Assinatura, em
[`../flows/001-ONBOARDING.md`](../flows/001-ONBOARDING.md).)*

## Eventos publicados por `identity_access` (Usuário, Papel, Sessão)

`domain/001-cadastros.md` já nomeava `UsuarioCriado`/`UsuarioDesativado`/`PapelCriado`/
`PapelAtualizado` como eventos "novos", e `domain/010-administracao.md` já nomeava
`SessaoDeAcessoIniciada`/`SessaoDeAcessoEncerrada` — nenhum dos cinco jamais foi catalogado aqui
(décima-segunda ocorrência da família D194/.../D327). Corrigido no Sprint 11, Lote 2, ao implementar
o primeiro código real de `identity_access` (D345) — antes deste lote não havia nenhum consumidor
de código para justificar fechar a lacuna, só documentação.

| Evento | Gerado quando | Consumido por |
|---|---|---|
| `UsuarioCriado` | `POST /users` cria um Usuário | `audit`, `notification_center` |
| `UsuarioDesativado` | `DELETE /users/{id}` (soft delete) | `audit`, `notification_center` |
| `PapelCriado` | `POST /roles` cria um Papel | `audit` |
| `PapelAtualizado` | `PATCH /roles/{id}` altera nome/descrição/permissões | `audit` |
| `SessaoDeAcessoIniciada` | `POST /auth/login` bem-sucedido | `audit` |
| `SessaoDeAcessoEncerrada` | `POST /auth/logout`, expiração, ou revogação administrativa | `audit` |

Reatribuição de Papéis a um Usuário (`usuarios_papeis`) e alteração do conjunto de Permissões de um
Papel (`papel_permissao`) **não** geram um evento de domínio próprio — nenhum dos dois foi nomeado
em `domain/001-cadastros.md`, e inventar um nome agora violaria D101/D103. Ambas as mudanças
continuam auditáveis via `logs_auditoria` diretamente (D344), que não depende de um evento de
domínio para funcionar — ver `docs/backend/core/IDENTITY_IMPLEMENTATION.md`.

## Eventos publicados por `integration` (Integrações, Webhooks, Jobs)

`domain/010-administracao.md` já nomeava `WebhookEntregue`/`WebhookFalhou`/`JobConcluido`/
`JobFalhou` como eventos "novos" desde o Sprint 09 — nunca catalogados aqui (D239-style,
décima-primeira ocorrência da família D194/.../D313). Corrigido no Sprint 10/Lote 12 (D327), ao
preparar `docs/api/088-webhooks.md`/`089-jobs.md`.

| Evento | Gerado quando | Consumido por |
|---|---|---|
| `WebhookEntregue` | Uma tentativa de entrega de webhook recebe resposta `2xx` do endpoint de destino. | `analytics`, `audit` |
| `WebhookFalhou` | Uma tentativa de entrega de webhook falha (timeout, erro, resposta não-`2xx`). | `notification_center` (alerta o responsável pela integração), `audit` |
| `JobConcluido` | Uma Execução de Job termina com `resultado = SUCESSO`. | `analytics`, `audit` |
| `JobFalhou` | Uma Execução de Job termina com `resultado = FALHA`. | `notification_center`, `audit` |

## Evento transversal — `audit`

| Evento | Gerado quando | Consumido por |
|---|---|---|
| `AcaoAuditada` | Qualquer evento acima é publicado (o bounded context `audit` assina **todos** os eventos do barramento, não apenas os listados aqui). | *(consumidor terminal — nunca republica)* |

---

## Regras deste mapa

- Um evento é sempre publicado por **exatamente um** bounded context — o dono do agregado que
  mudou de estado.
- `analytics` e `audit` são consumidores "terminais": podem assinar qualquer evento do barramento,
  mas nunca publicam eventos que outro bounded context precise consumir para funcionar (ver
  [`DEPENDENCY_MAP.md`](./DEPENDENCY_MAP.md), Camada 6 — nada depende deles).
- Todo evento novo — de um módulo já listado aqui ou de um módulo futuro — entra neste documento
  antes de ser implementado, com publicador, gatilho e consumidores definidos, para que a lista de
  consumers de cada exchange RabbitMQ seja conhecida antes do código existir.
- Este mapa cresce junto com [`../flows/`](../flows/): um evento entra aqui quando o fluxo que o
  gera é desenhado, não quando o módulo entra em desenvolvimento — por isso já cobre eventos de
  módulos V2/V3 (ex: `tracking`, `mobile`) cujos fluxos de negócio foram documentados à frente da
  implementação (ver [`MODULE_PRIORITY.md`](./MODULE_PRIORITY.md) para quando cada um será
  construído).
