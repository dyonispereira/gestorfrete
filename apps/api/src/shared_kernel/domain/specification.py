from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

TCandidate = TypeVar("TCandidate")


class Specification(ABC, Generic[TCandidate]):
    """Base class for the Specification pattern (D=business rule as an object).

    A Specification encapsulates a single predicate about a candidate object
    so query/filter rules can be composed and reused instead of scattered as
    ad-hoc boolean expressions across the application layer. Persistence-aware
    subclasses (e.g. translating to a SQLAlchemy ``WHERE`` clause) belong to
    each module's ``infrastructure/persistence`` — this base only guarantees
    the in-memory contract every specification must satisfy.
    """

    @abstractmethod
    def is_satisfied_by(self, candidate: TCandidate) -> bool: ...

    def __and__(self, other: "Specification[TCandidate]") -> "Specification[TCandidate]":
        return _AndSpecification(self, other)

    def __or__(self, other: "Specification[TCandidate]") -> "Specification[TCandidate]":
        return _OrSpecification(self, other)

    def __invert__(self) -> "Specification[TCandidate]":
        return _NotSpecification(self)


class _AndSpecification(Specification[TCandidate]):
    def __init__(self, left: Specification[TCandidate], right: Specification[TCandidate]) -> None:
        self._left = left
        self._right = right

    def is_satisfied_by(self, candidate: TCandidate) -> bool:
        return self._left.is_satisfied_by(candidate) and self._right.is_satisfied_by(candidate)


class _OrSpecification(Specification[TCandidate]):
    def __init__(self, left: Specification[TCandidate], right: Specification[TCandidate]) -> None:
        self._left = left
        self._right = right

    def is_satisfied_by(self, candidate: TCandidate) -> bool:
        return self._left.is_satisfied_by(candidate) or self._right.is_satisfied_by(candidate)


class _NotSpecification(Specification[TCandidate]):
    def __init__(self, inner: Specification[TCandidate]) -> None:
        self._inner = inner

    def is_satisfied_by(self, candidate: TCandidate) -> bool:
        return not self._inner.is_satisfied_by(candidate)
