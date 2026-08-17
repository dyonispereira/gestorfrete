# CONSTRAINTS.md — Catálogo de Constraints do Modelo Relacional

Todo `CHECK`/`NOT NULL`/`UNIQUE`/FK do Modelo Relacional, organizado pelas 8 categorias pedidas em
revisão — mas com um princípio que governa o documento inteiro, pedido explicitamente:

**Nem toda regra de negócio vira uma constraint SQL.** Cada linha abaixo tem uma coluna **Camada
Responsável**, porque confundir "isto o banco garante" com "isto a aplicação garante" é o tipo de
erro que só aparece depois, em produção. Quatro camadas possíveis:

| Camada | O que significa | Exemplo |
|---|---|---|
| **Banco** | `CHECK`/`NOT NULL`/`UNIQUE`/FK — impossível violar mesmo com acesso direto ao SQL | `contas_pagar.tenant_id NOT NULL` |
| **Aplicação** | Validado no backend antes de gravar — o banco aceitaria o dado inválido se a aplicação for contornada | "CIOT só pode ter Motorista com `TIPO_VINCULO = AUTONOMO`" (comentado em `007-fiscal.md`, nunca virou `CHECK`) |
| **Domínio** | Invariante de agregado, frequentemente multi-tabela ou multi-evento — não é responsabilidade de uma linha isolada | "Viagem só encerra quando os três ciclos (documental/operacional/financeiro) convergirem" — lógica do aggregate `Viagem`, nunca uma constraint física |
| **Evento/Processamento** | Mantido por um consumidor assíncrono, não pela transação de escrita original | `disponibilidade_veiculo` recalculada por consumidor de `ViagemDespachada`/`ViagemConcluida`; `status_aptidao` de `Motorista` recalculado quando `documentos_motorista` muda |

Regra de bolso usada para decidir onde cada constraint vive: **se a violação pode ser detectada
olhando só para as colunas da própria linha (ou de uma FK direta), vira `CHECK` no Banco. Se
depende de múltiplas linhas, múltiplas tabelas, ou de uma sequência de eventos no tempo, fica em
Aplicação/Domínio/Evento — nunca forçada para dentro de uma constraint SQL gigante.**

## Achado ao preparar este documento (D199)

Auditando todo par `vigencia_inicio`/`vigencia_fim` (e variantes `data_inicio_vigencia`/
`data_fim_vigencia`) do sistema contra a presença de um `CHECK (fim > inicio)`: `contratos_frete` e
`apolices_seguro_veicular` já tinham a proteção; `tabelas_preco`, `composicoes_veiculares`,
`equipamentos_rastreamento` e `parametros_tenant` não — mesmo padrão conceitual, 4 de 6 tabelas sem
a constraint física. Corrigido nos 4 arquivos `relational/` correspondentes antes deste catálogo.
Sétimo gap real encontrado por auditoria-contra-DDL nesta sprint (D193–D199) — o padrão continua
valendo a pena.

---

## 1. Integridade

`NOT NULL`, `CHECK` de linha única, FK — a base de "este dado não pode existir de forma
inconsistente", nunca a regra de negócio inteira.

| Regra | Constraint física | Camada |
|---|---|---|
| Toda tabela de negócio pertence a um tenant | `tenant_id UUID NOT NULL REFERENCES tenants(id)` (toda tabela, D174) | Banco |
| CT-e/MDF-e/CIOT não existem sem Viagem | `viagem_id UUID NOT NULL REFERENCES viagens(id)` | Banco |
| Documento do Motorista não existe sem Motorista | `motorista_id UUID NOT NULL REFERENCES motoristas(id)` | Banco |
| Item de lista não existe sem o pai (item de carga, item de cotação, item de OS, etc.) | FK `NOT NULL` para a tabela-pai (catálogo completo em [`FOREIGN_KEYS.md`](./FOREIGN_KEYS.md)) | Banco |
| Usuário vincula no máximo um de Motorista/Funcionário, nunca os dois | `ck_usuarios_motorista_xor_funcionario CHECK (NOT (motorista_id IS NOT NULL AND funcionario_id IS NOT NULL))` | Banco |
| Categoria de CNH só existe quando o documento é uma CNH | `ck_documentos_motorista_categoria_so_cnh CHECK (categoria_cnh IS NULL OR tipo_documento = 'CNH')` | Banco |
| Plano de Manutenção Preventiva tem um alvo (veículo específico OU categoria inteira) | `ck_planos_manutencao_preventiva_alvo CHECK (veiculo_tracionador_id IS NOT NULL OR categoria_veiculo_id IS NOT NULL)` | Banco |
| Fatura nasce de uma Viagem ou de uma Entrega (nunca nenhuma, nunca ambas por design de tela) | `ck_faturas_origem CHECK (viagem_id IS NOT NULL OR entrega_id IS NOT NULL)` — o "nunca ambas" fica em Aplicação, o banco só garante "pelo menos uma" | Banco (parcial) + Aplicação |
| Conta a Pagar com origem declarada tem a FK correspondente preenchida | `ck_contas_pagar_origem_especifica` (ver texto completo em `006-financeiro.md`) — D099 | Banco |
| Rateio de Despesa aponta para Centro de Custo ou Viagem | `ck_rateios_despesa_alvo CHECK (centro_custo_id IS NOT NULL OR viagem_id IS NOT NULL)` | Banco |
| Chave de acesso de NF-e tem exatamente 44 dígitos | `ck_nfe_referenciadas_chave_44_digitos CHECK (chave_acesso ~ '^[0-9]{44}$')` | Banco |
| CIOT só pode ter Motorista Autônomo | Comentário em `007-fiscal.md` (`ciots.motorista_id`) — nunca virou `CHECK` porque depende do valor de `tipo_vinculo` em `motoristas`, tabela diferente | Aplicação |
| Fornecedor executor de OS deve ter `tipo_principal` compatível com o tipo de serviço | Não modelado como constraint — validação de compatibilidade semântica, não de integridade referencial | Aplicação |
| Viagem só encerra quando os três ciclos (documental/operacional/financeiro) convergirem | Nenhuma constraint física — depende do estado de outras tabelas (`ctes`, `contas_receber`) e de regras do aggregate `Viagem` | Domínio |
| Alocação de recurso (Motorista+Veículo+Implemento) é sempre um bundle atômico por Viagem (D188) | `uq_alocacoes_recurso_viagem_vigente UNIQUE (viagem_id) WHERE status = 'VIGENTE'` garante uma só vigente; a coerência do bundle em si (não alocar veículo já em uso por outra Viagem simultânea) é validação cruzada | Banco (unicidade) + Aplicação (exclusividade de uso) |

## 2. Exclusividade

Já catalogado por completo em [`INDEXES.md`](./INDEXES.md) categoria 3 (69 `UNIQUE`) — não repetido
aqui linha a linha (D069-style, nunca duplicar o mesmo inventário em dois documentos). Resumo por
tipo de identificador, com a camada:

| Tipo de identificador | Exemplos | Camada |
|---|---|---|
| Documento oficial (CPF/CNPJ/RENAVAM/chassi) | `motoristas.cpf`, `clientes.cnpj_cpf`, `veiculos_tracionadores.renavam`, `fichas_tecnicas_veiculo.chassi` | Banco |
| Protocolo de integração externa (idempotência) | `ctes.protocolo_sefaz`, `ciots.protocolo_antt`, `eventos_fiscais.protocolo_externo`, `heartbeats.protocolo_externo` | Banco (ver categoria 6, mesma constraint serve dupla função) |
| Identificador funcional interno | `tenant_id + codigo` em toda tabela com `codigo` | Banco |
| Identificador de hardware/dispositivo | `equipamentos_rastreamento.identificador_serial`, `dispositivos_mobile.identificador_dispositivo` | Banco |
| "Marca de fogo" (fiscal, imutável por lei) | `ctes.chave_acesso`, `mdfes.chave_acesso`, `ciots.codigo_ciot` | Banco |
| Identificador local mobile (offline-first) | `filas_sincronizacao (sessao_mobile_id, identificador_local_unico)` | Banco |

## 3. Estados

Valores permitidos (`ENUM`), transições protegíveis pelo banco, e status derivados/`GENERATED`.

| Regra | Constraint física | Camada |
|---|---|---|
| Todo enum de status tem vocabulário fechado | `CREATE TYPE <tabela>_status_enum AS ENUM (...)` em toda tabela com estado | Banco |
| `viagens.encerrada` é sempre derivado, nunca editável diretamente | `GENERATED ALWAYS AS (...) STORED` (D072/D185) | Banco |
| Transição de status é sempre para frente, nunca retrocede (ex: CT-e `EMITIDO` não volta a `RASCUNHO`) | Nenhum `CHECK` — o banco não versiona a linha anterior numa `UPDATE` simples; a garantia real é a tabela `*_status_history` (append-only) registrar a sequência, e a aplicação validar a transição antes de gravar | Aplicação (a transição em si) + Banco (o histórico é imutável, nunca editado/apagado) |
| `status_aptidao` do Motorista é recalculado quando a CNH vence/é renovada | Não é `CHECK` — é recalculado por trigger ou lógica de aplicação ao mudar `documentos_motorista` (nota em `002-cadastros.md`) | Evento/Processamento |
| `disponibilidade_veiculo.status` reflete o despacho/conclusão de Viagem | Nenhuma FK de escrita direta — populada só por consumidor de evento (`ViagemDespachada`, `ViagemConcluida`, `OrdemServicoAberta`) | Evento/Processamento |
| Cerca Eletrônica tem exatamente a geometria do seu tipo (círculo tem centro+raio, polígono tem polígono) | `ck_cercas_eletronicas_geometria` (`CHECK` composto, `008-rastreamento.md`) | Banco |
| Conciliação Bancária aponta para exatamente um alvo (Conta a Pagar OU Conta a Receber) | `ck_conciliacoes_bancarias_alvo_exclusivo CHECK ((conta_pagar_id IS NOT NULL)::int + (conta_receber_id IS NOT NULL)::int = 1)` | Banco |
| Estorno Financeiro aponta para exatamente um alvo (Fatura, Conta a Pagar ou Conta a Receber) | `ck_estornos_financeiros_alvo_exclusivo` (mesmo padrão, 3 vias) | Banco |
| Agendamento de Atualização (BI) aponta para exatamente um alvo (Métrica OU Cubo Analítico) | `ck_agendamentos_atualizacao_alvo` (mesmo padrão, 2 vias) | Banco |
| Ordem de Serviço só tem `causa` preenchida quando `tipo = CORRETIVA` | `ck_ordens_servico_causa_so_corretiva CHECK (causa IS NULL OR tipo = 'CORRETIVA')` | Banco |

O padrão "exatamente N de M colunas preenchidas" (`(a IS NOT NULL)::int + (b IS NOT NULL)::int = 1`)
aparece 3 vezes de forma idêntica — vale como template reutilizável para qualquer FK-alternativa
futura, mesmo espírito de reuso já aplicado ao gate de confirmação humana (categoria 7).

## 4. Temporalidade

`data_inicio < data_fim`, vigência sem sobreposição, colunas derivadas de duas datas.

| Regra | Constraint física | Camada |
|---|---|---|
| Janela de Entrega: fim depois do início | `ck_janelas_entrega_hora_fim_apos_inicio CHECK (hora_fim > hora_inicio)` | Banco |
| Contrato de Frete: vigência coerente | `ck_contratos_frete_vigencia CHECK (vigencia_fim IS NULL OR vigencia_fim > vigencia_inicio)` | Banco |
| Apólice de Seguro Veicular: vigência coerente | `ck_apolices_seguro_veicular_vigencia CHECK (vigencia_fim > vigencia_inicio)` | Banco |
| Tabela de Preço: vigência coerente | `ck_tabelas_preco_vigencia` (D199, corrigido nesta preparação) | Banco |
| Composição Veicular: vigência coerente | `ck_composicoes_veiculares_vigencia` (D199) | Banco |
| Equipamento de Rastreamento: vigência coerente | `ck_equipamentos_rastreamento_vigencia` (D199, tolera início também nulo) | Banco |
| Parâmetro do Tenant: vigência coerente | `ck_parametros_tenant_vigencia` (D199) | Banco |
| Vigência sem sobreposição entre registros da mesma entidade (ex: dois Planos de Preço vigentes simultâneos para o mesmo Cliente) | Nenhum `CHECK`/`EXCLUDE` físico — exigiria `EXCLUDE USING gist` com faixas de data, avaliação de custo/benefício não feita ainda; hoje é responsabilidade da aplicação ao ativar um novo registro | Aplicação (candidato a `EXCLUDE` constraint em `PARTITIONING.md`/evolução futura, não decidido aqui) |
| Duração sempre calculada de duas colunas da mesma linha, nunca reescrita manualmente | `duracao_ms INTEGER GENERATED ALWAYS AS (EXTRACT(EPOCH FROM (fim - inicio)) * 1000) STORED` — `eventos_fiscais`, `registros_sincronizacao`, `inferencias_ia` | Banco |
| Margem prevista de Viagem é sempre `receita - custo` da mesma linha | `margem_prevista NUMERIC GENERATED ALWAYS AS (receita_prevista_snapshot - custo_previsto) STORED` | Banco |
| Valor total de item é sempre `quantidade × valor_unitário` da mesma linha | `valor_total NUMERIC GENERATED ALWAYS AS (quantidade * valor_unitario) STORED` (`itens_ordem_servico`) | Banco |
| Timestamps de Time Series (`capturado_em`/`recebido_em`/`processado_em`) coerentes entre si (captura nunca depois do recebimento) | Nenhum `CHECK` — a fonte externa pode enviar dados fora de ordem por natureza (rede móvel, buffer offline); forçar essa ordem no banco rejeitaria dados legítimos | Aplicação (validação de sanidade, não de integridade) |

## 5. Tenant

Já em vigor desde D174/D193/D195 ([`TENANCY_MODEL.md`](./TENANCY_MODEL.md)) — resumido aqui só como
índice de consulta rápida, não redecidido:

| Regra | Constraint física | Camada |
|---|---|---|
| Toda tabela de negócio tem `tenant_id NOT NULL` | FK para `tenants(id)`, `NOT NULL` (D174) | Banco |
| Exceção: Platform Reference Data não tem `tenant_id` | `permissoes`, `planos`, `itens_plano`, `origens_localizacao` — ausência documentada, não omissão (D046) | Banco (ausência deliberada) |
| Exceção: tabela de junção pura não precisa de `tenant_id` próprio | `papel_permissao`, `mdfes_ctes`, e demais (D193) — garantido pelos dois lados da junção | Banco |
| `tenant_id` da filha é sempre consistente com o do pai, nunca uma segunda origem da verdade | Não há `CHECK` cross-table nativo no PostgreSQL para isso — garantido pela aplicação no momento da escrita (D193, complemento pedido em revisão) | Aplicação (reforçável por trigger se `RLS` for adotado) |
| `tenant_id` nunca é `SET NULL`, mesmo quando a coluna é opcional (`modelos_ia`, `execucoes_job`) | `ON DELETE RESTRICT` universal em `tenant_id` (D195) — nulidade é decisão de escrita, nunca efeito colateral de exclusão | Banco |
| Isolamento de tenant é reforçado, não apenas confiado à aplicação | Row-Level Security (`RLS`) avaliado tabela a tabela como segunda camada — **não decidido globalmente**, permanece em aberto (`TENANCY_MODEL.md`) | Banco (se/quando ativado) — hoje é só Aplicação |

## 6. Idempotência

Toda chave física que existe especificamente para impedir duplicação de um evento/mensagem
externa — nunca só "regra de negócio", sempre um mecanismo de proteção contra reprocessamento
(rede instável, retry, mensagens fora de ordem).

| Origem da duplicação possível | Constraint física | Camada |
|---|---|---|
| SEFAZ reenviando o mesmo protocolo de autorização de CT-e/MDF-e | `uq_ctes_protocolo_sefaz`, `uq_mdfes_protocolo_sefaz` — `UNIQUE (...) WHERE protocolo_sefaz IS NOT NULL` | Banco |
| ANTT reenviando o mesmo protocolo de CIOT | `uq_ciots_protocolo_antt` | Banco |
| Qualquer evento fiscal reprocessado (protocolo repetido para o mesmo documento) | `uq_eventos_fiscais_documento_protocolo UNIQUE (documento_tipo, documento_id, protocolo_externo)` | Banco |
| Provedor de rastreamento reenviando o mesmo heartbeat | `uq_heartbeats_equipamento_protocolo` | Banco |
| App Motorista sincronizando o mesmo registro duas vezes (rede instável, offline-first) | `uq_filas_sincronizacao_identificador_local UNIQUE (sessao_mobile_id, identificador_local_unico)` (D111) | Banco |
| Token de API sendo gerado duas vezes com o mesmo hash | `uq_tokens_api_token_hash` (D084 — nunca reutilizado) | Banco |
| Webhook disparado mais de uma vez para o mesmo evento | Não modelado como constraint de unicidade — responsabilidade do consumidor do webhook (o padrão de mercado é o **destinatário** tratar idempotência via um `event_id` no payload), este sistema garante unicidade de *assinatura*, não de *entrega* | Aplicação (do lado de quem recebe o webhook, fora deste banco) |
| Job assíncrono (`execucoes_job`) executando duas vezes por retry do scheduler | Nenhuma `UNIQUE` — o padrão aqui é idempotência pelo *efeito* (o consumidor deve ser idempotente ao aplicar o resultado), não pela *linha de log* em si, que é sempre um novo registro de tentativa (`numero_tentativa` já existe como conceito de observabilidade, não de dedupe) | Aplicação/Evento |

## 7. Confirmação Humana

| Regra | Constraint física | Camada |
|---|---|---|
| Toda Aprovação de Custo/Despesa tem um ator humano, sempre — nunca uma aprovação "de ninguém" | `ator_id UUID NOT NULL REFERENCES usuarios(id)` (`aprovacoes_custo`, `aprovacoes_despesa`) — mais simples que o gate condicional abaixo porque a linha *é* a aprovação, não um status que pode ou não ter sido revisado | Banco |
| Leitura de Visão Computacional que exigia revisão humana não pode ficar num status terminal sem um usuário confirmando | `ck_leituras_visao_computacional_confirmacao_humana CHECK (status = 'PROCESSADA' OR revisao_humana_necessaria = FALSE OR usuario_confirmacao_id IS NOT NULL)` (D161/D164) — template reutilizável para qualquer futura saída de IA com o mesmo gate | Banco |
| Sugestão de IA aceita/rejeitada registra qual Usuário decidiu | `sugestoes_ia.usuario_decisao_id` — coluna nullable (nem toda sugestão foi decidida ainda), sem `CHECK` adicional porque não há um "status terminal que exige decisão" tão explícito quanto o caso de visão computacional | Aplicação |
| Assinatura Digital (motorista confirmando canhoto/entrega) sempre vinculada a um documento | `assinaturas_digitais` referencia `documento_tipo`/`documento_id` (polimórfico, sem FK física — mesma exceção de `enderecos`/`anexos`) | Aplicação (integridade da referência polimórfica) |

## 8. Soft Delete

Já em vigor desde D177 ([`SOFT_DELETE_MODEL.md`](./SOFT_DELETE_MODEL.md)) — resumido como índice:

| Regra | Constraint física | Camada |
|---|---|---|
| Toda tabela principal tem `excluido_em`/`excluido_por` nullable | Colunas presentes, nunca `NOT NULL` (seriam contraditórias) | Banco |
| Aplicação nunca emite `DELETE`, só `UPDATE excluido_em` | Nenhuma constraint impede um `DELETE` físico no banco — a garantia é 100% de disciplina de código (camada de repositório), não física | Aplicação |
| Exclusão lógica é distinta do status de negócio (ex: Veículo `INATIVO` ≠ Veículo excluído) | Duas colunas sempre separadas (`status` vs. `excluido_em`), nunca fundidas em uma só | Banco (estrutura) + Aplicação (semântica) |
| Índice único parcial nunca conta linha excluída como conflito | Todo `UNIQUE`/índice de negócio que poderia colidir com um registro logicamente apagado usa `WHERE excluido_em IS NULL` (catálogo completo em [`INDEXES.md`](./INDEXES.md) categoria 10) | Banco |
| `logs_auditoria` nunca tem soft delete — não existe cenário de "log sai de circulação" | Sem colunas `excluido_em`/`excluido_por` nesta tabela, de propósito (D109) | Banco (ausência deliberada) |

---

## Totais por camada (visão consolidada)

| Camada | Papel no sistema |
|---|---|
| **Banco** | Maioria das linhas acima — sempre que a violação é detectável olhando só a própria linha (ou uma FK direta) |
| **Aplicação** | Regras que dependem de outra tabela/outro valor não coberto por FK, ou de disciplina de código (nunca emitir `DELETE`) |
| **Domínio** | Invariantes de agregado que atravessam múltiplas entidades/eventos — a maior parte da complexidade de negócio real do sistema não é (e não deveria ser) uma constraint SQL |
| **Evento/Processamento** | Estado mantido por consumidor assíncrono, nunca pela transação de escrita original |

Este documento não é uma lista de "o que falta implementar em SQL" — as linhas marcadas
Aplicação/Domínio/Evento estão **corretamente** fora do banco; forçá-las para dentro de uma
constraint SQL geralmente as tornaria mais frágeis (`CHECK` não vê outras tabelas, não vê o tempo,
não vê eventos), não mais seguras.

## Como este documento cresce

Estável enquanto o Modelo Relacional não muda. Toda nova constraint física criada num
`relational/NNN.md` ganha uma linha na categoria certa aqui, com a Camada Responsável decidida
explicitamente — nunca assumida. Próximo documento da sequência:
[`PARTITIONING.md`](./PARTITIONING.md) (estratégia, retenção, arquivamento, compressão, índices
locais, manutenção, `VACUUM`/`ANALYZE`, rotação automática de partição).
