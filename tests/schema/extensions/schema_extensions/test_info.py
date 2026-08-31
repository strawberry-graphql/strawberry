from __future__ import annotations

import warnings
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from typing import Any

import pytest
from graphql import GraphQLResolveInfo

import strawberry
from strawberry.extensions import SchemaExtension
from strawberry.schema.config import StrawberryConfig
from strawberry.utils.await_maybe import await_maybe


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "world"


def test_resolve_receives_configured_strawberry_info() -> None:
    class CustomInfo(strawberry.Info): ...

    received_info: list[strawberry.Info] = []

    class Extension(SchemaExtension):
        def resolve(
            self,
            next_: Any,
            root: Any,
            info: strawberry.Info,
            **kwargs: Any,
        ) -> Any:
            received_info.append(info)
            return next_(root, info, **kwargs)

    schema = strawberry.Schema(
        query=Query,
        extensions=[Extension],
        config=StrawberryConfig(info_class=CustomInfo),
    )

    result = schema.execute_sync("{ hello }")

    assert result.errors is None
    assert result.data == {"hello": "world"}
    assert len(received_info) == 1
    assert isinstance(received_info[0], CustomInfo)
    assert received_info[0].field_name == "hello"


@pytest.mark.asyncio
async def test_async_resolve_receives_strawberry_info() -> None:
    received_info: list[strawberry.Info] = []

    class Extension(SchemaExtension):
        async def resolve(
            self,
            next_: Any,
            root: Any,
            info: strawberry.Info,
            **kwargs: Any,
        ) -> Any:
            received_info.append(info)
            return await await_maybe(next_(root, info, **kwargs))

    schema = strawberry.Schema(query=Query, extensions=[Extension])
    result = await schema.execute("{ hello }")

    assert result.errors is None
    assert result.data == {"hello": "world"}
    assert len(received_info) == 1
    assert isinstance(received_info[0], strawberry.Info)


def test_strawberry_info_extension_can_pass_raw_info_to_next() -> None:
    class Extension(SchemaExtension):
        def resolve(
            self,
            next_: Any,
            root: Any,
            info: strawberry.Info,
            **kwargs: Any,
        ) -> Any:
            return next_(root, info._raw_info, **kwargs)

    schema = strawberry.Schema(query=Query, extensions=[Extension])
    result = schema.execute_sync("{ hello }")

    assert result.errors is None
    assert result.data == {"hello": "world"}


def test_strawberry_and_graphql_info_extensions_can_be_mixed() -> None:
    received_info: list[tuple[str, object]] = []

    class StrawberryInfoExtension(SchemaExtension):
        def resolve(
            self,
            next_: Any,
            root: Any,
            info: strawberry.Info,
            **kwargs: Any,
        ) -> Any:
            received_info.append(("strawberry", info))
            return next_(root, info, **kwargs)

    class GraphQLInfoExtension(SchemaExtension):
        def resolve(
            self,
            next_: Any,
            root: Any,
            info: GraphQLResolveInfo,
            **kwargs: Any,
        ) -> Any:
            received_info.append(("graphql", info))
            return next_(root, info, **kwargs)

    schema = strawberry.Schema(
        query=Query,
        extensions=[StrawberryInfoExtension, GraphQLInfoExtension],
    )

    with pytest.warns(DeprecationWarning, match="GraphQLInfoExtension.resolve"):
        result = schema.execute_sync("{ hello }")

    assert result.errors is None
    assert {name for name, _ in received_info} == {"strawberry", "graphql"}
    strawberry_info = dict(received_info)["strawberry"]
    graphql_info = dict(received_info)["graphql"]
    assert isinstance(strawberry_info, strawberry.Info)
    assert strawberry_info._raw_info is graphql_info


def test_legacy_info_warning_is_emitted_once_per_extension_class() -> None:
    received_info: list[object] = []
    worker_count = 8

    class LegacyExtension(SchemaExtension):
        def resolve(self, next_: Any, root: Any, info: Any, **kwargs: Any) -> Any:
            received_info.append(info)
            return next_(root, info, **kwargs)

    schema = strawberry.Schema(query=Query, extensions=[LegacyExtension])
    barrier = Barrier(worker_count)

    def execute(_: int) -> Any:
        barrier.wait()
        return schema.execute_sync("{ hello }")

    with warnings.catch_warnings(record=True) as caught_warnings:
        warnings.simplefilter("always")
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            results = list(executor.map(execute, range(worker_count)))

    matching_warnings = [
        warning
        for warning in caught_warnings
        if "LegacyExtension.resolve receives GraphQLResolveInfo" in str(warning.message)
    ]
    assert len(matching_warnings) == 1
    assert all(result.errors is None for result in results)
    assert all(not isinstance(info, strawberry.Info) for info in received_info)
    assert all(info.field_name == "hello" for info in received_info)


def test_strawberry_info_extension_handles_graphql_core_only_fields() -> None:
    received_info: dict[str, strawberry.Info] = {}

    class Extension(SchemaExtension):
        def resolve(
            self,
            next_: Any,
            root: Any,
            info: strawberry.Info,
            **kwargs: Any,
        ) -> Any:
            received_info[info.field_name] = info
            return next_(root, info, **kwargs)

    schema = strawberry.Schema(query=Query, extensions=[Extension])
    result = schema.execute_sync("{ __typename hello }")

    assert result.errors is None
    assert result.data == {"__typename": "Query", "hello": "world"}
    assert set(received_info) == {"__typename", "hello"}
    assert received_info["__typename"].python_name == "__typename"
    assert received_info["__typename"].get_argument_definition("name") is None
    with pytest.raises(ValueError, match="has no Strawberry return type"):
        received_info["__typename"].return_type
