from __future__ import annotations

from typing import Any

from shared_kernel.application.command import Command, CommandHandler


class CommandHandlerNotRegisteredError(RuntimeError):
    """Raised when dispatching a Command with no handler registered for its type."""


class CommandHandlerAlreadyRegisteredError(RuntimeError):
    """Raised when two handlers try to register for the same Command type.

    CQRS requires exactly one handler per command — unlike events, a command
    is never fanned out to multiple listeners.
    """


class InMemoryCommandBus:
    """Process-local CommandBus: routes a Command to its single registered
    CommandHandler. Each module wires its own handlers into this bus during
    application startup (``main.py``'s composition root) — the bus itself
    knows nothing about any bounded context.
    """

    def __init__(self) -> None:
        self._handlers: dict[type[Command], CommandHandler[Any, Any]] = {}

    def register(self, command_type: type[Command], handler: CommandHandler[Any, Any]) -> None:
        if command_type in self._handlers:
            raise CommandHandlerAlreadyRegisteredError(
                f"A handler is already registered for {command_type.__name__}"
            )
        self._handlers[command_type] = handler

    async def dispatch(self, command: Command) -> Any:
        handler = self._handlers.get(type(command))
        if handler is None:
            raise CommandHandlerNotRegisteredError(
                f"No handler registered for {type(command).__name__}"
            )
        return await handler.handle(command)
