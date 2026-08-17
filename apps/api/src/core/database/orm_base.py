from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base shared by every bounded context's SQLAlchemy models
    (``modules/<contexto>/infrastructure/persistence/models/``). One shared
    ``Base.metadata`` is what lets ``alembic/env.py`` autogenerate migrations
    across the whole schema — each module still owns its own model classes,
    only the metadata registry is shared (``INFRASTRUCTURE_LAYER.md``).
    """
