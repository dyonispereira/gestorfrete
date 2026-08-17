from __future__ import annotations

from typing import Generic, TypeVar

TId = TypeVar("TId")


class BaseEntity(Generic[TId]):
    """Base class for every Entity in the system.

    Unlike a Value Object, an Entity has an identity (``id``) that persists
    across state changes over its lifetime. Two entities are equal when their
    identities are equal, regardless of the value of their other attributes.
    """

    def __init__(self, id: TId) -> None:
        self._id = id

    @property
    def id(self) -> TId:
        return self._id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseEntity):
            return NotImplemented
        if type(self) is not type(other):
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        return hash((type(self), self._id))
