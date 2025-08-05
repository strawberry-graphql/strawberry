import contextlib
import dataclasses
import enum
from collections.abc import AsyncGenerator
from typing import Any

import pytest

import strawberry
from strawberry.extensions import SchemaExtension


@dataclasses.dataclass
class SchemaHelper:
    query_type: type
    subscription_type: type
    query: str
    subscription: str


class ExampleExtension(SchemaExtension):
    def __init_subclass__(cls, **kwargs: Any):
        super().__init_subclass__(**kwargs)
        cls.called_hooks = []

    expected = [
        "on_operation Entered",
        "on_parse Entered",
        "on_parse Exited",
        "on_validate Entered",
        "on_validate Exited",
        "on_execute Entered",
        "resolve",
        "resolve",
        "on_execute Exited",
        "on_operation Exited",
        "get_results",
    ]
    called_hooks: list[str]

    @classmethod
    def assert_expected(cls) -> None:
        assert cls.called_hooks == cls.expected


@pytest.fixture
def default_query_types_and_query() -> SchemaHelper:
    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person()

    @strawberry.type
    class Subscription:
        @strawberry.subscription
        async def count(self) -> AsyncGenerator[int, None]:
            for i in range(5):
                yield i

    subscription = "subscription TestSubscribe { count }"
    query = "query TestQuery { person { name } }"
    return SchemaHelper(
        query_type=Query,
        query=query,
        subscription_type=Subscription,
        subscription=subscription,
    )


class ExecType(enum.Enum):
    SYNC = enum.auto()
    ASYNC = enum.auto()

    def is_async(self) -> bool:
        return self == ExecType.ASYNC


@pytest.fixture(params=[ExecType.ASYNC, ExecType.SYNC])
def exec_type(request: pytest.FixtureRequest) -> ExecType:
    return request.param


@contextlib.contextmanager
def hook_wrap(list_: list[str], hook_name: str):
    list_.append(f"{hook_name} Entered")
    try:
        yield
    finally:
        list_.append(f"{hook_name} Exited")


@pytest.fixture
def async_extension() -> type[ExampleExtension]:
    class MyExtension(ExampleExtension):
        async def on_operation(self):
            with hook_wrap(self.called_hooks, SchemaExtension.on_operation.__name__):
                yield

        async def on_validate(self):
            with hook_wrap(self.called_hooks, SchemaExtension.on_validate.__name__):
                yield

        async def on_parse(self):
            with hook_wrap(self.called_hooks, SchemaExtension.on_parse.__name__):
                yield

        async def on_execute(self):
            with hook_wrap(self.called_hooks, SchemaExtension.on_execute.__name__):
                yield

        async def get_results(self):
            self.called_hooks.append("get_results")
            return {"example": "example"}

        async def resolve(self, _next, root, info, *args: str, **kwargs: Any):
            self.called_hooks.append("resolve")
            return _next(root, info, *args, **kwargs)

    return MyExtension
