# 004 — Reference Data

Cadastros auxiliares (D036 — parte do universo **Referência**, mas distintos de Master Data —
ver [`002-MASTER_DATA.md`](./002-MASTER_DATA.md)): listas relativamente simples usadas para
classificar ou padronizar outros dados, não entidades de negócio ricas com identidade própria.

## Entidades de Reference Data

| Entidade | Bounded Context | Frequência de Alteração | Compartilhável no AgriHub |
|---|---|---|---|
| País | Global — ver discussão abaixo | Muito baixa | Sim |
| Estado | Global — ver discussão abaixo | Muito baixa | Sim |
| Município | Global — ver discussão abaixo | Muito baixa | Sim |
| Tipo de Combustível | `fleet` | Muito baixa | A avaliar — GestorPec pode ter um conceito análogo para maquinário agrícola |
| Categoria de Veículo | `fleet` | Muito baixa | Não |
| Tipo de Documento (fiscal) | `documents` | Muito baixa | Não |
| Motivos de Cancelamento | Ver nota abaixo — não é um cadastro único | Baixa | Não |

**Categoria Financeira/Plano de Contas** já está tratado em
[`002-MASTER_DATA.md`](./002-MASTER_DATA.md) — não duplicado aqui (princípio "não duplicar
informação", ver [`README.md`](./README.md)).

**Reconciliação de nomes**: o exemplo original desta etapa citava "Tipo de Veículo" e "Tipo de
Implemento" como cadastros separados. Já temos a entidade `Categoria de Veículo`
([`../domain/003-frota.md`](../domain/003-frota.md)), que já referencia tanto Veículo Tracionador
quanto Implemento — os dois conceitos do exemplo são o mesmo cadastro, não dois.

## Motivos de Cancelamento — não é um cadastro central único

Diferente das demais linhas, "Motivos de Cancelamento" não tem um dono único natural: Viagem
([`../flows/002-VIAGEM.md`](../flows/002-VIAGEM.md)), Ordem de Serviço
([`../flows/003-MANUTENCAO.md`](../flows/003-MANUTENCAO.md)) e Cotação
([`../domain/002-operacao.md`](../domain/002-operacao.md)) cancelam por motivos diferentes e não
comparáveis entre si. Pela regra de posse única (D033), a proposta é que **cada bounded context
mantenha seu próprio catálogo de motivos** (`MotivoCancelamentoViagem`, `MotivoCancelamentoOS`,
etc.), em vez de um cadastro central compartilhado — um cadastro único forçaria `freight` e
`maintenance` a coordenar mudanças em uma lista que não pertence a nenhum dos dois de fato. Fica
como recomendação registrada aqui; não é uma decisão que precisa de um número `D0xx` próprio porque
é uma aplicação direta de D033, não uma regra nova.

## Dados de referência globais (sem tenant) — resolvido como Platform Reference Data (D046)

País, Estado e Município foram os primeiros dados que este projeto encontrou que não deveriam ter
`tenant_id` — são os mesmos para todos os tenants da plataforma (o Estado de São Paulo não muda de
nome porque é uma transportadora diferente consultando). A exceção proposta aqui foi aprovada e
formalizada como decisão: **D046 — Platform Reference Data**, uma categoria oficial de dado sem
`tenant_id`, compartilhado entre todos os tenants, somente leitura para clientes, atualizável
apenas pela plataforma (migrações/administração global). Ver
[`../product/DECISIONS.md`](../product/DECISIONS.md), D046, e também D047 (três níveis de posse —
este é o Nível 1, Plataforma) e D048 (Seed Data, distinta de Master Data).

Exemplos oficiais de Platform Reference Data (D046): Países, Estados, Municípios, feriados
nacionais (quando implementados), moedas (futuro), fusos horários, códigos IBGE, códigos ISO,
códigos ANTT padronizados, lista oficial de UFs.

O dono técnico continua sem um bounded context de negócio associado — por definição (D046), este
tipo de dado não pertence a nenhum dos 30 bounded contexts congelados, é mantido pela própria
plataforma (seed/migração), não por um módulo de domínio.

**Compartilhamento no AgriHub**: por serem dados globais e não específicos do GestorFrete, País/
Estado/Município continuam sendo os candidatos mais óbvios e de menor risco a compartilhamento
entre todos os produtos do ecossistema — mais simples que Usuário/Tenant (ver
[`002-MASTER_DATA.md`](./002-MASTER_DATA.md)), por não carregarem nenhum dado sensível ou
específico de negócio.

## Frequência de alteração como sinal de estratégia de cache

O motivo prático de registrar "Frequência de Alteração" em todo este documento: toda entidade
listada aqui tem frequência **Muito baixa** — são os melhores candidatos do sistema para cache
agressivo (inclusive cache local no app do motorista, útil junto com D039, Offline First seletivo)
e para não gerarem `StatusHistory` (D017/D018) — uma mudança de nome de município, por exemplo, é
rara o bastante para não precisar de uma máquina de estados, apenas auditoria simples (D007).
