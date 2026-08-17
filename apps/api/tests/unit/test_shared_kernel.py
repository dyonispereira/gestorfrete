from __future__ import annotations

import uuid
from dataclasses import dataclass

import pytest

from shared_kernel.application.command import Command, CommandHandler
from shared_kernel.application.command_bus import (
    CommandHandlerAlreadyRegisteredError,
    CommandHandlerNotRegisteredError,
    InMemoryCommandBus,
)
from shared_kernel.application.query import Query, QueryHandler
from shared_kernel.application.query_bus import InMemoryQueryBus, QueryHandlerNotRegisteredError
from shared_kernel.domain.base_aggregate_root import BaseAggregateRoot
from shared_kernel.domain.base_entity import BaseEntity
from shared_kernel.domain.domain_event import DomainEvent
from shared_kernel.domain.result import Result
from shared_kernel.domain.specification import Specification


class TestBaseEntity:
    def test_two_entities_with_same_id_are_equal_even_with_different_attributes(self) -> None:
        entity_id = uuid.uuid4()
        a = BaseEntity(entity_id)
        b = BaseEntity(entity_id)
        assert a == b

    def test_entities_of_different_types_are_never_equal(self) -> None:
        class Foo(BaseEntity[uuid.UUID]):
            pass

        class Bar(BaseEntity[uuid.UUID]):
            pass

        entity_id = uuid.uuid4()
        assert Foo(entity_id) != Bar(entity_id)

    def test_entity_is_not_equal_to_non_entity(self) -> None:
        assert BaseEntity(uuid.uuid4()) != "not-an-entity"


class TestBaseAggregateRoot:
    def test_pull_domain_events_returns_and_clears_recorded_events(self) -> None:
        aggregate = BaseAggregateRoot(uuid.uuid4())
        event = DomainEvent()
        aggregate.record_event(event)

        pulled = aggregate.pull_domain_events()

        assert pulled == [event]
        assert aggregate.pull_domain_events() == []


class TestResult:
    def test_ok_result_exposes_value_and_is_success(self) -> None:
        result: Result[int, str] = Result.ok(42)
        assert result.is_success
        assert not result.is_failure
        assert result.value == 42

    def test_fail_result_exposes_error_and_is_failure(self) -> None:
        result: Result[int, str] = Result.fail("boom")
        assert result.is_failure
        assert result.error == "boom"

    def test_accessing_value_of_a_failed_result_raises(self) -> None:
        result: Result[int, str] = Result.fail("boom")
        with pytest.raises(ValueError):
            _ = result.value

    def test_accessing_error_of_a_successful_result_raises(self) -> None:
        result: Result[int, str] = Result.ok(1)
        with pytest.raises(ValueError):
            _ = result.error


@dataclass(frozen=True)
class _IsEven(Specification[int]):
    def is_satisfied_by(self, candidate: int) -> bool:
        return candidate % 2 == 0


@dataclass(frozen=True)
class _IsPositive(Specification[int]):
    def is_satisfied_by(self, candidate: int) -> bool:
        return candidate > 0


class TestSpecification:
    def test_and_combinator(self) -> None:
        spec = _IsEven() & _IsPositive()
        assert spec.is_satisfied_by(4)
        assert not spec.is_satisfied_by(-4)
        assert not spec.is_satisfied_by(3)

    def test_or_combinator(self) -> None:
        spec = _IsEven() | _IsPositive()
        assert spec.is_satisfied_by(-4)
        assert spec.is_satisfied_by(3)
        assert not spec.is_satisfied_by(-3)

    def test_not_combinator(self) -> None:
        spec = ~_IsEven()
        assert spec.is_satisfied_by(3)
        assert not spec.is_satisfied_by(4)


@dataclass(frozen=True)
class _Ping(Command):
    value: str


class _PingHandler(CommandHandler[_Ping, str]):
    async def handle(self, command: _Ping) -> str:
        return f"pong:{command.value}"


@dataclass(frozen=True)
class _GetValue(Query):
    key: str


class _GetValueHandler(QueryHandler[_GetValue, str]):
    async def handle(self, query: _GetValue) -> str:
        return f"value-of:{query.key}"


class TestInMemoryCommandBus:
    async def test_dispatch_routes_to_the_registered_handler(self) -> None:
        bus = InMemoryCommandBus()
        bus.register(_Ping, _PingHandler())

        result = await bus.dispatch(_Ping(value="hello"))

        assert result == "pong:hello"

    def test_registering_two_handlers_for_the_same_command_raises(self) -> None:
        bus = InMemoryCommandBus()
        bus.register(_Ping, _PingHandler())

        with pytest.raises(CommandHandlerAlreadyRegisteredError):
            bus.register(_Ping, _PingHandler())

    async def test_dispatching_an_unregistered_command_raises(self) -> None:
        bus = InMemoryCommandBus()

        with pytest.raises(CommandHandlerNotRegisteredError):
            await bus.dispatch(_Ping(value="hello"))


class TestInMemoryQueryBus:
    async def test_dispatch_routes_to_the_registered_handler(self) -> None:
        bus = InMemoryQueryBus()
        bus.register(_GetValue, _GetValueHandler())

        result = await bus.dispatch(_GetValue(key="x"))

        assert result == "value-of:x"

    async def test_dispatching_an_unregistered_query_raises(self) -> None:
        bus = InMemoryQueryBus()

        with pytest.raises(QueryHandlerNotRegisteredError):
            await bus.dispatch(_GetValue(key="x"))
