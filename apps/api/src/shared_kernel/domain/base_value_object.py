from __future__ import annotations

from abc import ABC


class BaseValueObject(ABC):
    """Base class for every Value Object in the system.

    A Value Object has no identity: two instances are equal when all of their
    attributes are equal. Concrete value objects should be declared as
    ``@dataclass(frozen=True)`` subclasses so equality and immutability come
    for free from the dataclass machinery.
    """
