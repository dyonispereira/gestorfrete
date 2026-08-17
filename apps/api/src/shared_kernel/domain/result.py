from __future__ import annotations

from typing import Generic, TypeVar

TValue = TypeVar("TValue")
TError = TypeVar("TError")


class Result(Generic[TValue, TError]):
    """Either/Result pattern used across the domain and application layers.

    Use cases and domain operations that can fail with an *expected* business
    error (as opposed to an unexpected exception) return a ``Result`` instead
    of raising, keeping failure paths explicit in the type signature.
    """

    def __init__(self, *, value: TValue | None, error: TError | None, is_success: bool) -> None:
        self._value = value
        self._error = error
        self._is_success = is_success

    @classmethod
    def ok(cls, value: TValue) -> "Result[TValue, TError]":
        return cls(value=value, error=None, is_success=True)

    @classmethod
    def fail(cls, error: TError) -> "Result[TValue, TError]":
        return cls(value=None, error=error, is_success=False)

    @property
    def is_success(self) -> bool:
        return self._is_success

    @property
    def is_failure(self) -> bool:
        return not self._is_success

    @property
    def value(self) -> TValue:
        if not self._is_success:
            raise ValueError("Cannot access .value of a failed Result")
        return self._value  # type: ignore[return-value]

    @property
    def error(self) -> TError:
        if self._is_success:
            raise ValueError("Cannot access .error of a successful Result")
        return self._error  # type: ignore[return-value]
