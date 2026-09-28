# PRODUCTION_DEPLOYMENT.md — Procedimento de migration e segurança de rede do piloto

Production Readiness Hardening — formaliza dois procedimentos que antes só existiam implicitamente
(rodados manualmente em CI/local, nunca escritos como um procedimento a seguir em produção):
migration segura (Parte 7) e firewall/segurança de rede (Parte 9). Não descreve como provisionar a
VPS em si — isso é a próxima etapa (Provisionamento + primeiro deploy).

## Procedimento de migration

Alembic nunca roda sozinho neste projeto — confirmado no Discovery de Ambiente: nenhum
`entrypoint.sh`, nenhum hook de startup em `main.py` chama `alembic upgrade head`. Isso é
deliberado, não um gap: uma migration é uma decisão de deploy, nunca algo que deva rodar sem
supervisão sempre que um container reinicia.

Sequência obrigatória, sempre nesta ordem:

```
1. scripts/backup.sh                              # backup local
2. scripts/backup_offsite_copy.sh <dump>           # segunda localização (Parte 8)
3. docker compose -f infra/compose/docker-compose.prod.yml \
     --env-file infra/compose/.env.prod \
     exec api poetry run alembic upgrade head       # migration em si
4. curl -f https://api.<dominio>/health/ready        # confirma que tudo continua saudável
5. Só então: considerar o deploy liberado
```

Se o passo 3 falhar no meio (migration parcialmente aplicada), **não tentar rodar de novo
imediatamente** — cada migration deste repositório tem `downgrade()` real (confirmado: 24/24
migrations verificadas, nenhum stub), então o caminho seguro é `alembic downgrade -1` explícito,
investigar a causa, só então tentar de novo. O backup do passo 1/2 é o último recurso, não o
primeiro — reverter uma migration quase sempre é mais rápido que restaurar o banco inteiro.

**Nunca duas migrations simultâneas.** Alembic aqui usa configuração padrão (confirmado em
`alembic/env.py`) — sem lock distribuído, só a tabela `alembic_version` como guarda implícita. Para
o piloto (processo de deploy único, sem múltiplos pipelines concorrentes) isso é um risco baixo na
prática, mas é uma regra operacional, não uma garantia do código: **só um processo de deploy
executa `alembic upgrade head` por vez**, nunca dois deploys/ambientes apontando para o mesmo banco
simultaneamente.

## Segurança de rede — firewall de produção

| Porta | Exposição | Serviço |
|---|---|---|
| `443/tcp` | **Pública** | Caddy — único ponto de entrada HTTP(S) real |
| `80/tcp` | **Pública** | Caddy — só desafio ACME (emissão/renovação de certificado) e redirect automático para 443 |
| `22/tcp` | **Administração**, conforme a política de acesso definida no deploy (nunca aberta a `0.0.0.0/0` sem justificativa — VPN/allowlist de IP é o padrão recomendado) | SSH do host |
| `5432/tcp` (Postgres) | **Nunca pública** | Nem publicada no host (`docker-compose.prod.yml`), nem alcançável pela rede `edge` — só `internal`, mesma rede que `api` |
| `6379/tcp` (Redis) | **Nunca pública** | Mesma garantia de `5432` — só rede `internal` |
| `9000/tcp` (MinIO, API de dados) | **Nunca uma porta pública direta** | Alcançável de fora só via `https://files.<dominio>` (Caddy → rede `edge` → `minio:9000`) — nunca a porta 9000 exposta cru no host |
| `9001/tcp` (MinIO Console) | **Nunca pública, nem via proxy** | Sem bloco de site no `Caddyfile` para o console administrativo — deliberadamente inacessível de fora da rede Docker |
| `5672/15672/tcp` (RabbitMQ) | **N/A no piloto** | RabbitMQ não sobe (`docker-compose.prod.yml` não declara o serviço) — Parte 2 |

O acesso ao MinIO pelo navegador (upload/download via URL assinada, D314) acontece **somente**
através de `https://files.<dominio>` — nunca um IP:porta direto. Isso é garantido estruturalmente
pela topologia de rede do `docker-compose.prod.yml` (`postgres`/`redis` nunca entram na rede
`edge`; `minio`/`api` entram em `edge` **e** `internal`; `web`/`caddy` só em `edge`) — não depende
de disciplina manual de quem configura o firewall do host, o isolamento já existe um nível abaixo,
na rede Docker.

## Checklist de verificação pós-deploy

- [ ] `curl -f https://api.<dominio>/health/ready` retorna `200` com todos os checks habilitados
      em `true` (ou `"disabled"` só para `rabbitmq`, nunca para `database`/`redis`/`storage`)
- [ ] `curl -I https://app.<dominio>` retorna `200`/`30x` com certificado TLS válido (não
      autoassinado — Caddy já deveria ter emitido um real via ACME)
- [ ] `curl https://api.<dominio>/docs` retorna `404` (Parte 4 — nunca deve estar acessível em
      produção)
- [ ] `nmap`/`nc` confirmando que `5432`/`6379`/`9001` não respondem do lado de fora do host
- [ ] `docker compose -f infra/compose/docker-compose.prod.yml ps` mostra todos os serviços
      `healthy`, nenhum em `restarting`/`unhealthy`
