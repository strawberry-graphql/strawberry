from __future__ import annotations

from typing import TYPE_CHECKING, AsyncGenerator, Tuple, Type
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

import strawberry

if TYPE_CHECKING:
    from strawberry.extensions.tracing.sentry import (
        SentryTracingExtension,
        SentryTracingExtensionSync,
    )


@pytest.fixture
def sentry_extension(
    mocker: MockerFixture,
) -> Tuple[Type[SentryTracingExtension], MagicMock]:
    sentry_mock = mocker.MagicMock()

    mocker.patch.dict("sys.modules", sentry_sdk=sentry_mock)

    from strawberry.extensions.tracing.sentry import SentryTracingExtension

    return SentryTracingExtension, sentry_mock


@pytest.fixture
def sentry_extension_sync(
    mocker: MockerFixture,
) -> Tuple[Type[SentryTracingExtension], MagicMock]:
    sentry_mock = mocker.MagicMock()

    mocker.patch.dict("sys.modules", sentry_sdk=sentry_mock)

    from strawberry.extensions.tracing.sentry import SentryTracingExtensionSync

    return SentryTracingExtensionSync, sentry_mock


@strawberry.type
class Person:
    name: str = "Jack"


@strawberry.type
class Query:
    @strawberry.field
    def person(self) -> Person:
        return Person()

    @strawberry.field
    async def person_async(self) -> Person:
        return Person()


@strawberry.type
class Mutation:
    @strawberry.mutation
    def say_hi(self) -> str:
        return "hello"


@strawberry.type
class Subscription:
    @strawberry.field
    async def on_hi(self) -> AsyncGenerator[str, None]:
        yield "Hello"


@pytest.mark.asyncio
async def test_sentry_tracer(
    sentry_extension: Tuple[SentryTracingExtension, MagicMock], mocker: MockerFixture
):
    extension, mock = sentry_extension

    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        extensions=[extension],
    )

    query = """
        query {
            personAsync {
                name
            }
        }
    """

    with pytest.warns(
        DeprecationWarning, match="The Sentry tracing extension is deprecated"
    ):
        await schema.execute(query)

    assert mock.configure_scope.mock_calls == [
        mocker.call(),
        mocker.call().__enter__(),
        mocker.call().__enter__().span.__bool__(),
        mocker.call()
        .__enter__()
        .span.start_child(op="gql", description="Anonymous Query"),
        mocker.call().__exit__(None, None, None),
        mocker.call()
        .__enter__()
        .span.start_child()
        .set_tag("graphql.operation_type", "query"),
        mocker.call()
        .__enter__()
        .span.start_child()
        .set_tag("graphql.resource_name", "63a280256ca4e8514e06cf90b30c8c3a"),
        mocker.call().__enter__().span.start_child().set_data("graphql.query", query),
        mocker.call()
        .__enter__()
        .span.start_child()
        .start_child(op="parsing", description="Parsing"),
        mocker.call().__enter__().span.start_child().start_child().finish(),
        mocker.call()
        .__enter__()
        .span.start_child()
        .start_child(op="validation", description="Validation"),
        mocker.call().__enter__().span.start_child().start_child().finish(),
        mocker.call()
        .__enter__()
        .span.start_child()
        .start_child(op="resolve", description="Resolving: Query.personAsync"),
        mocker.call().__enter__().span.start_child().start_child().__enter__(),
        mocker.call()
        .__enter__()
        .span.start_child()
        .start_child()
        .__enter__()
        .set_tag("graphql.field_name", "personAsync"),
        mocker.call()
        .__enter__()
        .span.start_child()
        .start_child()
        .__enter__()
        .set_tag("graphql.parent_type", "Query"),
        mocker.call()
        .__enter__()
        .span.start_child()
        .start_child()
        .__enter__()
        .set_tag("graphql.field_path", "Query.personAsync"),
        mocker.call()
        .__enter__()
        .span.start_child()
        .start_child()
        .__enter__()
        .set_tag("graphql.path", "personAsync"),
        mocker.call()
        .__enter__()
        .span.start_child()
        .start_child()
        .__exit__(None, None, None),
        mocker.call().__enter__().span.start_child().finish(),
    ]


@pytest.mark.asyncio
async def test_uses_operation_name(
    sentry_extension: Tuple[SentryTracingExtension, MagicMock],
):
    extension, mock = sentry_extension

    schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=[extension])

    query = """
        query MyExampleQuery {
            person {
                name
            }
        }
    """

    with pytest.warns(
        DeprecationWarning, match="The Sentry tracing extension is deprecated"
    ):
        await schema.execute(query, operation_name="MyExampleQuery")

    mock.configure_scope().__enter__().span.start_child.assert_any_call(
        op="gql", description="MyExampleQuery"
    )


@pytest.mark.asyncio
async def test_uses_operation_type(
    sentry_extension: Tuple[SentryTracingExtension, MagicMock],
):
    extension, mock = sentry_extension

    schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=[extension])

    query = """
        mutation MyMutation {
            sayHi
        }
    """

    with pytest.warns(
        DeprecationWarning, match="The Sentry tracing extension is deprecated"
    ):
        await schema.execute(query, operation_name="MyMutation")

    mock.configure_scope().__enter__().span.start_child().set_tag.assert_any_call(
        "graphql.operation_type", "mutation"
    )


@pytest.mark.asyncio
async def test_uses_operation_subscription(
    sentry_extension: Tuple[SentryTracingExtension, MagicMock],
):
    extension, mock = sentry_extension

    schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=[extension])

    query = """
        subscription MySubscription {
            onHi
        }
    """

    with pytest.warns(
        DeprecationWarning, match="The Sentry tracing extension is deprecated"
    ):
        await schema.execute(query, operation_name="MySubscription")

    mock.configure_scope().__enter__().span.start_child().set_tag.assert_any_call(
        "graphql.operation_type", "subscription"
    )


def test_sentry_tracer_sync(
    sentry_extension_sync: Tuple[SentryTracingExtensionSync, MagicMock],
    mocker: MockerFixture,
):
    extension, mock = sentry_extension_sync
    schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=[extension])

    query = """
        query {
            person {
                name
            }
        }
    """

    with pytest.warns(
        DeprecationWarning, match="The Sentry tracing extension is deprecated"
    ):
        schema.execute_sync(query)

    assert mock.configure_scope.mock_calls == [
        mocker.call(),
        mocker.call().__enter__(),
        mocker.call().__enter__().span.__bool__(),
        mocker.call()
        .__enter__()
        .span.start_child(op="gql", description="Anonymous Query"),
        mocker.call().__exit__(None, None, None),
        mocker.call()
        .__enter__()
        .span.start_child()
        .set_tag("graphql.operation_type", "query"),
        mocker.call()
        .__enter__()
        .span.start_child()
        .set_tag("graphql.resource_name", "659edba9e6ac9c20d03da1b2d0f9a956"),
        mocker.call().__enter__().span.start_child().set_data("graphql.query", query),
        mocker.call()
        .__enter__()
        .span.start_child()
        .start_child(op="parsing", description="Parsing"),
        mocker.call().__enter__().span.start_child().start_child().finish(),
        mocker.call()
        .__enter__()
        .span.start_child()
        .start_child(op="validation", description="Validation"),
        mocker.call().__enter__().span.start_child().start_child().finish(),
        mocker.call()
        .__enter__()
        .span.start_child()
        .start_child(op="resolve", description="Resolving: Query.person"),
        mocker.call().__enter__().span.start_child().start_child().__enter__(),
        mocker.call()
        .__enter__()
        .span.start_child()
        .start_child()
        .__enter__()
        .set_tag("graphql.field_name", "person"),
        mocker.call()
        .__enter__()
        .span.start_child()
        .start_child()
        .__enter__()
        .set_tag("graphql.parent_type", "Query"),
        mocker.call()
        .__enter__()
        .span.start_child()
        .start_child()
        .__enter__()
        .set_tag("graphql.field_path", "Query.person"),
        mocker.call()
        .__enter__()
        .span.start_child()
        .start_child()
        .__enter__()
        .set_tag("graphql.path", "person"),
        mocker.call()
        .__enter__()
        .span.start_child()
        .start_child()
        .__exit__(None, None, None),
        mocker.call().__enter__().span.start_child().finish(),
    ]


def test_uses_operation_name_sync(
    sentry_extension_sync: Tuple[SentryTracingExtensionSync, MagicMock],
):
    extension, mock = sentry_extension_sync

    schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=[extension])

    query = """
        query MyExampleQuery {
            person {
                name
            }
        }
    """

    with pytest.warns(
        DeprecationWarning, match="The Sentry tracing extension is deprecated"
    ):
        schema.execute_sync(query, operation_name="MyExampleQuery")

    mock.configure_scope().__enter__().span.start_child.assert_any_call(
        op="gql", description="MyExampleQuery"
    )


def test_uses_operation_type_sync(
    sentry_extension_sync: Tuple[SentryTracingExtensionSync, MagicMock],
):
    extension, mock = sentry_extension_sync

    schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=[extension])

    query = """
        mutation MyMutation {
            sayHi
        }
    """

    with pytest.warns(
        DeprecationWarning, match="The Sentry tracing extension is deprecated"
    ):
        schema.execute_sync(query, operation_name="MyMutation")

    mock.configure_scope().__enter__().span.start_child().set_tag.assert_any_call(
        "graphql.operation_type", "mutation"
    )
