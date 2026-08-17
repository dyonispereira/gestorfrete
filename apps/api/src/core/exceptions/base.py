from __future__ import annotations


class ApplicationError(Exception):
    """Base class for every expected, business-meaningful error raised by
    this application. Maps 1:1 to a category in ``docs/api/ERROR_MODEL.md`` —
    every subclass below carries the HTTP status that category defines, so
    the FastAPI exception handler (``core/exceptions/handlers.py``) never has
    to guess which status code to return.

    ``code`` must be ``SCREAMING_SNAKE_CASE`` prefixed by the bounded context
    in English (D011), e.g. ``FREIGHT_TRIP_NOT_FOUND`` — callers in each
    module pass their own ``code``/``message``; this base class never
    hardcodes one except for the generic infrastructure-level subclasses
    below, which are not owned by any single bounded context.
    """

    http_status: int = 500

    def __init__(self, code: str, message: str, details: list[dict[str, str]] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or []


class ValidationError(ApplicationError):
    """400 — payload sintaticamente inválido (ERROR_MODEL.md, categoria
    Validação). Reservado para violações que a validação Pydantic do
    Controller não pega sozinha; o ``VALIDATION_FAILED`` automático de
    payload malformado é gerado pelo handler de ``RequestValidationError``
    do FastAPI, nunca por esta classe diretamente.
    """

    http_status = 400


class AuthenticationError(ApplicationError):
    """401 — autenticação ausente, inválida ou expirada (ERROR_MODEL.md,
    categoria Autenticação). Não faz parte da lista de 7 exceções pedida
    explicitamente pelo usuário — adicionada porque ``ERROR_MODEL.md`` (fonte
    de verdade já congelada, D209) distingue 401 (Autenticação) de 403
    (Autorização) como categorias diferentes; ``AuthorizationError`` sozinha
    não cobre "token ausente/expirado". Ver ``docs/backend/ERROR_HANDLING.md``.
    """

    http_status = 401


class AuthorizationError(ApplicationError):
    """403 — autenticado, mas sem a Permissão/Escopo necessário (D212,
    ERROR_MODEL.md categoria Autorização)."""

    http_status = 403


class NotFoundError(ApplicationError):
    """404 — recurso inexistente ou pertencente a outro tenant (nunca 403
    nesse segundo caso — ver a "Nota de segurança" em ERROR_MODEL.md)."""

    http_status = 404


class ConflictError(ApplicationError):
    """409 — estado atual conflita com a operação pedida (ex.: violação de
    unicidade, ``Idempotency-Key`` reaproveitada com payload diferente)."""

    http_status = 409


class DomainError(ApplicationError):
    """422 — payload válido, mas viola um invariante de domínio
    (ERROR_MODEL.md categoria "Regra de negócio")."""

    http_status = 422


class IntegrationError(ApplicationError):
    """502/504 — falha ao comunicar com um sistema externo (SEFAZ, ANTT,
    gateway de pagamento, provedor de rastreamento). ``http_status`` default
    502 (Bad Gateway); passe ``http_status=504`` no raise específico quando a
    falha for de timeout, não de resposta de erro."""

    def __init__(
        self,
        code: str,
        message: str,
        details: list[dict[str, str]] | None = None,
        http_status: int = 502,
    ) -> None:
        super().__init__(code, message, details)
        self.http_status = http_status


class InfrastructureError(ApplicationError):
    """500 — falha de infraestrutura própria (banco, cache, fila, storage)
    não prevista como regra de negócio. Sempre logada com ``request_id``,
    nunca detalhada ao cliente (ERROR_MODEL.md, "erro interno")."""

    http_status = 500

    def __init__(
        self,
        code: str = "INFRASTRUCTURE_ERROR",
        message: str = "Falha interna de infraestrutura.",
        details: list[dict[str, str]] | None = None,
    ) -> None:
        super().__init__(code, message, details)


# Alias mantido por compatibilidade com o nome já usado na fundação (Fase 0)
# — nunca dois nomes divergentes para o mesmo conceito daqui em diante, mas
# remover o nome antigo agora quebraria qualquer import já escrito contra
# ele sem necessidade real.
DomainRuleViolationError = DomainError
