# 002 — Master Data

Quais entidades do GestorFrete são Master Data (D036 — **Referência**): identidade estável, mudam
pouco, e por isso exigem governança diferente de uma entidade transacional. Usa os nomes e bounded
contexts já estabelecidos em [`../domain/`](../domain/) — nenhuma entidade nova é inventada aqui.

## Entidades de Master Data

| Entidade | Bounded Context | Frequência de Alteração | Compartilhável no AgriHub |
|---|---|---|---|
| Cliente | `crm` | Baixa | Não (dado comercial específico do GestorFrete) |
| Contato do Cliente | `crm` | Baixa | Não |
| Fornecedor | `maintenance` | Baixa | Não |
| Motorista | `drivers` | Baixa | Não (específico do domínio de transporte) |
| Veículo Tracionador | `fleet` | Baixa | Não |
| Implemento | `fleet` | Baixa | Não |
| Seguradora | `fleet` | Muito baixa | A avaliar — seguradoras também seguram rebanho no GestorPec |
| Filial | `tenancy` | Baixa | Não (estrutura organizacional é por produto) |
| Centro de Custo | `financial` | Baixa | Não |
| Tabela de Preço | `pricing` | Média | Não |
| Usuário | `identity_access` | Baixa | **Sim — forte candidato** |
| Papel | `identity_access` | Baixa | Parcial — mecanismo de RBAC sim, papéis específicos não |
| Permissão | `identity_access` | Muito baixa | Parcial — mesmo raciocínio de Papel |
| Funcionário | `identity_access` | Baixa | Parcial — a mesma pessoa pode atuar em operações que usam mais de um produto AgriHub |
| Categoria de Veículo | `fleet` | Muito baixa | Não |
| Modelo de Pneu | `maintenance` | Muito baixa | Não |
| Tipo de Serviço | `maintenance` | Muito baixa | Não |
| Tenant (Empresa) | `tenancy` | Muito baixa | **Sim — forte candidato** |
| Plano de Contas / Categoria Financeira | `financial` (detalhamento em `006-financeiro.md`, ainda não escrito) | Muito baixa | Parcial — planos de contas contábeis têm estrutura comum, mas cada produto tem contas específicas |

## Governança de Master Data

Master Data exige regras que dado transacional não exige, porque um erro aqui se propaga para
todas as transações futuras que o referenciam:

- **Deduplicação**: antes de criar um novo registro (ex: um Cliente), verificar se já existe um
  correspondente (CNPJ/CPF) — nunca depender só do usuário lembrar.
- **Alteração controlada**: mudanças em Master Data são raras o suficiente para justificar
  auditoria mais rigorosa que a padrão (D007) — quem alterou e por quê fica sempre visível, mesmo
  que a entidade em si não tenha uma máquina de estados (D015).
- **Impacto em cascata é sempre por referência, nunca por cópia**: quando um dado de Master Data
  muda (ex: razão social do Cliente), registros transacionais antigos que dependem do valor
  *daquele momento* usam Snapshot (D038, ver [`../domain/002-operacao.md`](../domain/002-operacao.md),
  Viagem) — nunca ficam "presos" a uma versão desatualizada por acidente, nem são reescritos
  silenciosamente.
- **Um dono, sempre** (D033/D034): Master Data nunca tem dois bounded contexts mantendo cópias
  próprias do mesmo cadastro.

## Compartilhamento futuro no ecossistema AgriHub

Duas entidades desta lista são candidatas fortes a se tornarem **Master Data de plataforma**
(compartilhadas entre GestorFrete, GestorPec e o futuro GestorContábil), não apenas de produto:

- **Usuário** — autenticação/identidade unificada é um objetivo estratégico de longo prazo (ver
  [`../product/VISION.md`](../product/VISION.md), capítulo 18, Ecossistema AgriHub): a mesma pessoa
  logando em mais de um produto do ecossistema sem recadastro.
- **Tenant (Empresa)** — o mesmo grupo econômico pode ser cliente de mais de um produto AgriHub
  simultaneamente; um cadastro de empresa unificado no nível do ecossistema evitaria recadastro e
  divergência de dados cadastrais/fiscais da própria empresa cliente.

**Observação em aberto, não decidida aqui**: o exemplo dado nesta revisão incluía "Pessoa" como
candidata a entidade compartilhada — hoje o GestorFrete não tem uma entidade `Pessoa` unificada
(Motorista, Contato do Cliente e Funcionário são entidades separadas, cada uma em seu bounded
context, por D033). Unificar essas três sob um conceito `Pessoa` de plataforma é uma mudança
estrutural real, não apenas documental, e esbarra diretamente na arquitetura congelada (D011) e na
regra de posse única (D033). Registro isto como tensão a resolver **quando** a integração com
GestorPec/GestorContábil for desenhada de fato (ver `VISION.md`, capítulos 19–20, "contrato técnico
ainda não definido") — não como uma mudança a fazer agora.

Endereço, Município, Estado e País — também citados no exemplo desta revisão — são **Dados de
Referência**, não Master Data; a análise de compartilhamento deles está em
[`004-REFERENCE_DATA.md`](./004-REFERENCE_DATA.md).
