from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

TResult = TypeVar("TResult")


class Command(ABC):
    """Marker base class for every Command (CQRS write side).

    A Command represents an intent to change the state of the system.
    Concrete commands should be declared as ``@dataclass(frozen=True)``
    subclasses carrying only the data needed to perform the action.
    """


TCommand = TypeVar("TCommand", bound=Command)


class CommandHandler(ABC, Generic[TCommand, TResult]):
    """Base class for the handler that executes a single Command."""

    @abstractmethod
    async def handle(self, command: TCommand) -> TResult: ...
