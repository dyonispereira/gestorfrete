# Domain-Driven Design (DDD)

## Por que DDD para este projeto

Um ERP para transportadoras não é um CRUD simples: fretes têm regras (um frete não pode ser
despachado sem motorista e veículo compatível habilitados), documentos fiscais têm regras
regulatórias, financeiro tem regras de conciliação. DDD nos dá vocabulário e técnica para modelar
essa complexidade em vez de escondê-la em código de infraestrutura.

## Bounded Contexts

Um **bounded context** é uma fronteira dentro da qual um modelo de domínio e sua linguagem são
consistentes. Fora dela, o mesmo termo pode significar outra coisa. Por isso o backend
(`apps/api/src/modules/`) e o frontend (`apps/web/src/modules/`) são organizados por bounded
context, não por tipo técnico de arquivo.

Os 10 bounded contexts originais desta fundação (operação central de uma transportadora):

| Módulo | Responsabilidade |
|---|---|
| `tenancy` | Transportadoras (tenants) e suas configurações de conta — a raiz do isolamento multi-tenant |
| `identity_access` | Usuários, papéis e permissões (RBAC); fundação de autenticação (JWT) |
| `fleet` | Veículos e frota |
| `drivers` | Motoristas |
| `freight` | Fretes, cargas e embarques — **core domain**: o motivo de o sistema existir |
| `routing` | Rotas e integração com Mapbox |
| `financial` | Contas a pagar/receber, faturamento, repasses |
| `documents` | Documentos fiscais (CT-e/MDF-e) e armazenamento de arquivos (MinIO) |
| `maintenance` | Manutenção preventiva/corretiva de veículos |
| `notifications` | Notificações e o barramento de eventos entre bounded contexts |

`freight` é marcado como **core domain**: é onde a maior parte do esforço de modelagem e da
atenção de produto deve se concentrar, porque é o que diferencia o GestorFrete de um ERP genérico.
Os demais são *supporting subdomains* (dão suporte ao core) ou *generic subdomains* (resolvidos de
forma parecida em qualquer sistema, como `identity_access`).

### Os 20 bounded contexts adicionais

Adicionados posteriormente à fundação (mesma estrutura de 4 camadas, apenas esqueleto — nenhuma
entidade ou regra foi modelada em nenhum deles ainda). Eles se dividem em dois grupos:

**Camada comercial do próprio SaaS** (cobram/gerenciam a transportadora como cliente da
plataforma GestorFrete, distintos da operação de transporte da transportadora):

| Módulo | Responsabilidade |
|---|---|
| `billing` | Cobrança/faturas da assinatura da transportadora na plataforma |
| `subscription` | Planos e assinaturas das transportadoras na plataforma |
| `pricing` | Precificação de fretes e tabelas de preço |
| `onboarding` | Fluxo de integração de novas transportadoras à plataforma |
| `landing` | Conteúdo institucional/marketing público, fora da área autenticada |

**Suporte, expansão e capacidades transversais de produto**:

| Módulo | Responsabilidade |
|---|---|
| `analytics` | BI e métricas agregadas entre bounded contexts |
| `crm` | Relacionamento comercial com clientes/embarcadores (leads, contatos, oportunidades) |
| `marketplace` | Publicação/captação de cargas entre transportadoras e embarcadores |
| `audit` | Trilha de auditoria de ações e alterações no sistema |
| `workflow` | Motor de fluxos de aprovação e automações configuráveis |
| `integration` | Integrações com sistemas externos (ERPs de clientes, SEFAZ, seguradoras) |
| `telemetry` | Telemetria de uso da aplicação e de dispositivos |
| `tracking` | Rastreamento em tempo real de veículos e cargas (distinto de `routing`) |
| `reporting` | Geração e exportação de relatórios (PDF/Excel) |
| `support` | Central de suporte e atendimento ao cliente (tickets, SAC) |
| `ai` | Recursos de inteligência artificial da plataforma |
| `mobile` | Contratos e casos de uso específicos do app mobile do motorista |
| `settings` | Configurações gerais da conta e preferências de usuário |
| `storage` | Arquivos e anexos genéricos (distinto de `documents`, que é fiscal) |
| `notification_center` | Inbox de notificações do usuário final (distinto de `notifications`, o barramento de eventos) |

Vários desses módulos têm nomes próximos de módulos já existentes propositalmente distintos —
`tracking` vs. `routing`, `storage` vs. `documents`, `notification_center` vs. `notifications`,
`billing`/`pricing` vs. `financial`, `settings` vs. `tenancy`. Cada README/`__init__.py` do módulo
documenta essa distinção explicitamente para evitar confusão na hora de decidir onde uma nova
entidade deve morar.

## Ubiquitous Language

Cada bounded context usa os termos do negócio de transporte em seu próprio vocabulário (frete,
CT-e, MDF-e, canhoto, praça de pedágio, etc.), e esse vocabulário deve ser usado literalmente no
código (nomes de entidades, métodos, eventos) — não traduzido para termos técnicos genéricos como
`Item` ou `Record`. Isso é o que torna o código legível para quem entende o negócio, não só para
quem entende programação.

O dicionário oficial de nomenclatura — qual nome usar em cada camada (negócio/UI vs. código/API), e
quais sinônimos são proibidos — é [`../domain/UBIQUITOUS_LANGUAGE.md`](../domain/UBIQUITOUS_LANGUAGE.md),
distinto de [`../product/GLOSSARY.md`](../product/GLOSSARY.md) (que explica o que os termos
significam, não como nomeá-los).

## Por que os bounded contexts não se importam diretamente uns aos outros

Um módulo nunca importa código de `domain/` ou `application/` de outro módulo diretamente — isso
recriaria o acoplamento que o DDD tático tenta evitar. Quando um bounded context precisa reagir a
algo que acontece em outro (ex: `financial` reage a um frete concluído em `freight`), a comunicação
acontece via Domain Event publicado no barramento (ver [`event-driven.md`](./event-driven.md)),
nunca via chamada de função entre módulos.
