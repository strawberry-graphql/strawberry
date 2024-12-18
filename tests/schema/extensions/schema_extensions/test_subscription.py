from collections.abc import AsyncGenerator

import pytest

import strawberry
from strawberry.extensions import SchemaExtension
from strawberry.types.execution import ExecutionResult
from tests.conftest import skip_if_gql_32

from .conftest import ExampleExtension, SchemaHelper

pytestmark = skip_if_gql_32(
    "We only fully support schema extensions in graphql-core 3.3+"
)


def assert_agen(obj) -> AsyncGenerator[ExecutionResult, None]:
    assert isinstance(obj, AsyncGenerator)
    return obj


async def test_subscription_success_many_fields(
    default_query_types_and_query: SchemaHelper, async_extension: type[ExampleExtension]
) -> None:
    schema = strawberry.Schema(
        query=default_query_types_and_query.query_type,
        subscription=default_query_types_and_query.subscription_type,
        extensions=[async_extension],
    )
    subscription_per_yield_hooks_exp = []
    for _ in range(5):  # number of yields in the subscription
        subscription_per_yield_hooks_exp.extend(["resolve", "get_results"])

    async_extension.expected = [
        "on_operation Entered",
        "on_parse Entered",
        "on_parse Exited",
        "on_validate Entered",
        "on_validate Exited",
        "on_execute Entered",
        "on_execute Exited",
        *subscription_per_yield_hooks_exp,
        # last one doesn't call the "resolve" / "get_results" hooks because
        # the subscription is done
        "on_operation Exited",
    ]
    async for res in assert_agen(
        await schema.subscribe(default_query_types_and_query.subscription)
    ):
        assert res.data
        assert not res.errors

    async_extension.assert_expected()


async def test_subscription_extension_handles_immediate_errors(
    default_query_types_and_query: SchemaHelper, async_extension: type[ExampleExtension]
) -> None:
    @strawberry.type()
    class Subscription:
        @strawberry.subscription()
        async def count(self) -> AsyncGenerator[int, None]:
            raise ValueError("This is an error")

    schema = strawberry.Schema(
        query=default_query_types_and_query.query_type,
        subscription=Subscription,
        extensions=[async_extension],
    )
    async_extension.expected = [
        "on_operation Entered",
        "on_parse Entered",
        "on_parse Exited",
        "on_validate Entered",
        "on_validate Exited",
        "on_execute Entered",
        "on_execute Exited",
        "get_results",
        "on_operation Exited",
    ]

    res = await schema.subscribe(default_query_types_and_query.subscription)
    assert res.errors

    async_extension.assert_expected()


async def test_error_after_first_yield_in_subscription(
    default_query_types_and_query: SchemaHelper, async_extension: type[ExampleExtension]
) -> None:
    @strawberry.type()
    class Subscription:
        @strawberry.subscription()
        async def count(self) -> AsyncGenerator[int, None]:
            yield 1
            raise ValueError("This is an error")

    schema = strawberry.Schema(
        query=default_query_types_and_query.query_type,
        subscription=Subscription,
        extensions=[async_extension],
    )

    agen = await schema.subscribe(default_query_types_and_query.subscription)
    assert isinstance(agen, AsyncGenerator)
    res1 = await agen.__anext__()
    assert res1.data
    assert not res1.errors
    res2 = await agen.__anext__()
    assert not res2.data
    assert res2.errors
    # close the generator
    with pytest.raises(StopAsyncIteration):
        await agen.__anext__()
    async_extension.expected = [
        "on_operation Entered",
        "on_parse Entered",
        "on_parse Exited",
        "on_validate Entered",
        "on_validate Exited",
        "on_execute Entered",
        "on_execute Exited",
        "resolve",
        "get_results",
        "get_results",
        "on_operation Exited",
    ]
    async_extension.assert_expected()


async def test_extensions_results_are_cleared_between_subscription_yields(
    default_query_types_and_query: SchemaHelper,
) -> None:
    class MyExtension(SchemaExtension):
        execution_number = 0

        def get_results(self):
            self.execution_number += 1
            return {str(self.execution_number): self.execution_number}

    schema = strawberry.Schema(
        query=default_query_types_and_query.query_type,
        subscription=default_query_types_and_query.subscription_type,
        extensions=[MyExtension],
    )

    res_num = 1

    async for res in assert_agen(
        await schema.subscribe(default_query_types_and_query.subscription)
    ):
        assert res.extensions == {str(res_num): res_num}
        assert not res.errors
        res_num += 1


async def test_subscription_catches_extension_errors(
    default_query_types_and_query: SchemaHelper,
) -> None:
    class MyExtension(SchemaExtension):
        def on_execute(self):
            raise ValueError("This is an error")

    schema = strawberry.Schema(
        query=default_query_types_and_query.query_type,
        subscription=default_query_types_and_query.subscription_type,
        extensions=[MyExtension],
    )
    async for res in assert_agen(
        await schema.subscribe(default_query_types_and_query.subscription)
    ):
        assert res.errors
        assert not res.data
        assert res.errors[0].message == "This is an error"
