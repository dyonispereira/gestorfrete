# AUTHORIZATION_IMPLEMENTATION.md — `AuthorizationService`

Conecta `AuthenticatedActor` (Foundation, Lote 1) a `RBAC_MATRIX.md` (404 permissões, congelado).
Vive em `modules/identity_access/application/authorization_service.py` — é lógica de aplicação do
bounded context que **possui** RBAC (`identity_access`), nunca um serviço genérico em `core/`
(`core` nunca conhece regra de negócio, `DEPENDENCY_RULES.md`; RBAC é regra de negócio real,
D051-D062, não infraestrutura transversal).

## Assinatura

```python
class AuthorizationService:
    async def authorize(self, actor: AuthenticatedActor, permission_code: str) -> None:
        """Levanta AuthorizationError(403, "IDENTITY_PERMISSION_DENIED") se o actor não tiver o
        código. Nunca retorna um booleano — chamar sem checar o retorno seria um bug silencioso
        fácil de esquecer; levantar força o chamador a lidar com a negativa (ou deixar propagar
        para o exception handler, ERROR_HANDLING.md)."""

    async def get_permission_codes(self, actor: AuthenticatedActor) -> frozenset[str]:
        """Usado quando o Controller precisa do conjunto inteiro (ex.: GET /auth/me montar a UI) —
        nunca para decidir autorização em código de aplicação (isso é sempre authorize())."""
```

## Resolução — sempre ao vivo, nunca do JWT (D340)

```
actor.user_id
     ↓  usuarios_papeis (SqlAlchemy, WHERE usuario_id = actor.user_id)
role_ids
     ↓  papel_permissao (WHERE papel_id IN role_ids)
permission_ids
     ↓  permissoes (WHERE id IN permission_ids)
permission_codes: frozenset[str]
     ↓
permission_code in permission_codes ?  → autorizado : AuthorizationError
```

Três `JOIN`s, uma query — nunca resolvido a partir de um claim do token. **D340, testado
explicitamente**: um token emitido antes de uma mudança de Papel deve refletir a mudança na
requisição seguinte, sem esperar o token expirar — só é possível porque o JWT nunca carrega a
lista de permissões como fonte de verdade (ver [`SESSION_IMPLEMENTATION.md`](./SESSION_IMPLEMENTATION.md)).

## Cache — por requisição, nunca entre requisições

O conjunto de códigos é resolvido uma vez por requisição (memoizado no próprio `AuthorizationService`
enquanto ele vive, escopado à requisição via injeção de dependência do FastAPI — uma instância nova
por chamada, mesmo padrão de `SQLAlchemyUnitOfWork`) — nunca cacheado em Redis/memória entre
requisições nesta etapa. Cache entre requisições é uma otimização futura, condicionada a um
mecanismo de invalidação por evento (`PapeisDoUsuarioAlterados`) que não existe ainda — adicionar o
cache sem a invalidação criaria uma janela real de RBAC desatualizado, pior que não ter cache
nenhum.

## Múltiplos Papéis — união, nunca interseção

Usuário com Papel A (`{x, y}`) e Papel B (`{y, z}`) tem permissões efetivas `{x, y, z}` — a query
acima já produz isso naturalmente (`IN role_ids` sobre `papel_permissao`, sem `INTERSECT`). Testado
explicitamente (`Multiple Roles`, critério de conclusão do usuário).

## `require_permission` — dependency FastAPI

```python
def require_permission(code: str) -> Callable:
    async def _dependency(
        actor: AuthenticatedActor = Depends(get_current_actor),
        authz: AuthorizationService = Depends(get_authorization_service),
    ) -> AuthenticatedActor:
        await authz.authorize(actor, code)
        return actor
    return _dependency
```

Uso no router: `Depends(require_permission("identity_access.user.view"))` — mesmo padrão em todo
router deste lote e de todos os futuros (Lote 3 em diante). Encadeia com `get_current_actor`
(`INTERFACES_LAYER.md`, Lote 1) — nunca duplica a resolução de JWT, só adiciona a checagem de
código sobre o actor já resolvido.

## Escopo (D051-D062) — o que este lote resolve, o que fica para depois

`RBAC_MATRIX.md` define Escopos (Empresa inteira/Filial/Unidade/Centro de Custo/Frota/Próprio
usuário) além do código de permissão puro. Neste lote, os recursos existentes (`Tenant`/`Usuário`/
`Papel`/`Permissão`) só usam dois: **Empresa inteira** (o padrão — qualquer Usuário com o código
certo vê/edita qualquer registro do próprio tenant) e **Próprio usuário** (`GET /auth/me`, sem RBAC
adicional além de estar autenticado). `AuthorizationService.authorize()` cobre só verbo+código —
filtragem por Filial/Centro de Custo/Frota não tem nenhum recurso deste lote para testar contra, e
implementar a abstração agora seria antecipar sem um caso de uso real (mesmo princípio de D206 —
não construir sobre um caso hipotético). Fica registrado para quando `fleet`/`financial` (Escopo
Frota/Centro de Custo) forem implementados.

## `Repository não decide autorização` (D341)

Nenhum `Repository` (`UserRepository`, `TenantRepository`, ...) recebe um `actor` ou chama
`AuthorizationService` — a decisão de "pode ou não" sempre acontece **antes** do Repository ser
usado, na camada de Application (Command/QueryHandler) ou na dependency do router. O Repository
resolve **o quê** existe (filtrado por tenant, `DOMAIN_LAYER.md`), nunca **quem pode ver**.

## Testes obrigatórios

- `authorize()` com o código certo: não levanta.
- `authorize()` sem o código: `AuthorizationError` (`403`, `IDENTITY_PERMISSION_DENIED`).
- Papel alterado no meio de uma sessão: próxima requisição já reflete o novo conjunto (sem
  reautenticar) — prova viva de D340.
- Dois Papéis: união testada com um caso concreto (Papel A dá `.view`, Papel B dá `.edit`, actor
  com os dois tem ambos).
- `get_permission_codes()` usado por `GET /auth/me` bate exatamente com o que `authorize()` decidiria
  código a código (mesma fonte, nunca duas implementações divergentes).
