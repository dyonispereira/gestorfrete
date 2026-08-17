# ADR 0003: Docker Compose para infraestrutura local (sem schema/dados)

## Status
Aceito

## Contexto
A stack depende de quatro serviços de infraestrutura desde o início: PostgreSQL, Redis, RabbitMQ e
MinIO. Nesta etapa de fundação nenhum schema de banco, migration ou dado de negócio deve existir —
mas os desenvolvedores precisam de um jeito consistente de subir esses serviços localmente assim
que começarem a implementar os próximos estágios (persistência, mensageria, storage).

## Decisão
Incluir `infra/compose/docker-compose.yml` com os quatro serviços como containers vazios
(imagens oficiais, volumes nomeados, healthchecks), sem qualquer inicialização de schema/tabela.
Isso é setup de ambiente de desenvolvimento, não desenvolvimento de banco/API.

## Alternativas consideradas
- **Não incluir infraestrutura nesta etapa**: adiaria a fundação de ambiente local para uma
  próxima etapa, mas deixaria a fundação arquitetural sem como ser validada localmente (nem mesmo
  o `docker compose config` para validar a topologia declarada).

## Consequências
- `infra/compose/docker-compose.yml` — os 4 serviços com portas padrão expostas ao host.
- `infra/compose/.env.example` — credenciais padrão de desenvolvimento (nunca usadas em produção).
- `infra/docker/api/Dockerfile` e `infra/docker/web/Dockerfile` — Dockerfiles multi-stage das duas
  aplicações, prontos porém ainda não integrados a um pipeline de CI/CD (fora do escopo desta
  etapa).
