# Multi-Tenancy

## Premissa

O GestorFrete atenderá **milhares de transportadoras**, cada uma com seus próprios dados —
fretes, veículos, motoristas, documentos e finanças de uma transportadora nunca podem vazar para
outra. Isolamento de tenant não é uma feature: é uma invariante de segurança que precisa ser
impossível de esquecer, em qualquer camada, por qualquer desenvolvedor, em qualquer módulo futuro.

## Estratégia de isolamento (decisão fundamental)

Para esta fundação, adota-se **isolamento lógico por coluna `tenant_id`** em vez de schema-per-
tenant ou database-per-tenant:

- Com milhares de tenants, schema/database-per-tenant se torna operacionalmente inviável
  (milhares de migrations a rodar, milhares de conexões/pools a gerenciar).
- Isolamento por coluna, aplicado de forma consistente, escala para milhares de tenants em um
  único cluster PostgreSQL (com possibilidade futura de particionamento/sharding por `tenant_id`
  se a escala exigir).

Toda entidade que pertence a uma transportadora carrega um `tenant_id` (o bounded context
`tenancy` é o dono da entidade `Tenant`). Esta é uma decisão arquitetural registrada aqui; qualquer
mudança de estratégia deve ser tratada como uma decisão de arquitetura tão significativa quanto
esta, não uma escolha de implementação de uma feature isolada.

## Tenant Context (`core/multitenancy/context.py`)

O tenant da requisição corrente é resolvido uma vez (futuramente, por um middleware que lê o
tenant a partir do JWT ou de um cabeçalho/domínio) e propagado via `ContextVar` durante toda a
requisição. Qualquer código — repositório, handler de Command/Query, publisher de evento — pode
chamar `get_current_tenant_id()` para saber "de quem" é a operação corrente, sem precisar receber o
tenant explicitamente por parâmetro em cada função.

`TenantNotSetError` é levantado propositalmente quando código que precisa de tenant roda sem um —
isso transforma "esqueci de filtrar por tenant" de um bug silencioso de vazamento de dados em um
erro que quebra imediatamente e de forma ruidosa.

## O que isso implica para bounded contexts futuros

Quando os primeiros modelos SQLAlchemy forem criados (`infrastructure/persistence/models/`), todos
que representam dados por-tenant devem incluir `tenant_id` e os repositórios concretos devem
filtrar por `get_current_tenant_id()` em toda leitura e escrita — nunca confiar que o chamador vai
lembrar de filtrar manualmente em cada query. Essa é uma regra de implementação a ser aplicada
consistentemente quando o Repository Pattern for implementado, e deve ser revisada com o mesmo
rigor de uma revisão de segurança.
