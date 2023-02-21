from typing import AsyncGenerator
from unittest.mock import call, patch

import pytest

import strawberry


@pytest.fixture
@patch("aws_xray_sdk.core.xray_recorder")
def xray_extension(mock_xray_recorder):
    from strawberry.extensions.tracing.xray import XRayExtension

    mock_xray_recorder.max_trace_back = 1

    return XRayExtension, mock_xray_recorder


@pytest.fixture
@patch("aws_xray_sdk.core.xray_recorder")
def xray_extension_sync(mock_xray_recorder):
    from strawberry.extensions.tracing.xray import XRayExtensionSync

    mock_xray_recorder.max_trace_back = 1

    return XRayExtensionSync, mock_xray_recorder


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


# TODO: this test could be improved by passing a custom tracer to the datadog extension
# and maybe we could unify datadog and opentelemetry extensions by doing that


@pytest.mark.asyncio
async def test_xray_tracer(xray_extension, mocker):
    extension, mock_xray_recorder = xray_extension

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

    await schema.execute(query)

    assert mock_xray_recorder.mock_calls == [
        call.begin_subsegment(name="GraphQL Query"),
        call.begin_subsegment().put_annotation("component", "graphql"),
        call.begin_subsegment().put_annotation(
            "query",
            "\n        query {\n            personAsync {\n                name\n            }\n        }\n    ",  # noqa: E501
        ),
        call.in_subsegment_async("GraphQL Resolving: personAsync"),
        call.in_subsegment_async().__aenter__(),
        call.in_subsegment_async().__aenter__().put_annotation("component", "graphql"),
        call.in_subsegment_async()
        .__aenter__()
        .put_annotation("graphql_parentType", "Query"),
        call.in_subsegment_async()
        .__aenter__()
        .put_annotation("graphql_path", "personAsync"),
        call.in_subsegment_async().__aexit__(None, None, None),
        call.end_subsegment(),
    ]


@pytest.mark.asyncio
async def test_uses_operation_name_and_hash(xray_extension):
    extension, mock_xray_recorder = xray_extension

    schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=[extension])

    query = """
        query MyExampleQuery {
            person {
                name
            }
        }
    """

    await schema.execute(query, operation_name="MyExampleQuery")

    assert mock_xray_recorder.mock_calls == [
        call.begin_subsegment(name="GraphQL Query: MyExampleQuery"),
        call.begin_subsegment().put_annotation("component", "graphql"),
        call.begin_subsegment().put_annotation(
            "query",
            "\n        query MyExampleQuery {\n            person {\n                name\n            }\n        }\n    ",  # noqa: E501
        ),
        call.in_subsegment_async("GraphQL Resolving: person"),
        call.in_subsegment_async().__aenter__(),
        call.in_subsegment_async().__aenter__().put_annotation("component", "graphql"),
        call.in_subsegment_async()
        .__aenter__()
        .put_annotation("graphql_parentType", "Query"),
        call.in_subsegment_async()
        .__aenter__()
        .put_annotation("graphql_path", "person"),
        call.in_subsegment_async().__aexit__(None, None, None),
        call.end_subsegment(),
    ]


@pytest.mark.asyncio
async def test_uses_operation_type(xray_extension):
    extension, mock_xray_recorder = xray_extension

    schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=[extension])

    query = """
        mutation MyMutation {
            sayHi
        }
    """

    await schema.execute(query, operation_name="MyMutation")

    assert mock_xray_recorder.mock_calls == [
        call.begin_subsegment(name="GraphQL Query: MyMutation"),
        call.begin_subsegment().put_annotation("component", "graphql"),
        call.begin_subsegment().put_annotation(
            "query",
            "\n        mutation MyMutation {\n            sayHi\n        }\n    ",
        ),
        call.in_subsegment_async("GraphQL Resolving: sayHi"),
        call.in_subsegment_async().__aenter__(),
        call.in_subsegment_async().__aenter__().put_annotation("component", "graphql"),
        call.in_subsegment_async()
        .__aenter__()
        .put_annotation("graphql_parentType", "Mutation"),
        call.in_subsegment_async().__aenter__().put_annotation("graphql_path", "sayHi"),
        call.in_subsegment_async().__aexit__(None, None, None),
        call.end_subsegment(),
    ]


@pytest.mark.asyncio
async def test_uses_operation_subscription(xray_extension):
    extension, mock_xray_recorder = xray_extension

    schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=[extension])

    query = """
        subscription MySubscription {
            onHi
        }
    """

    await schema.execute(query, operation_name="MySubscription")
    assert all(
        x in mock_xray_recorder.mock_calls
        for x in [
            call.begin_subsegment(name="GraphQL Query: MySubscription"),
            call.begin_subsegment().put_annotation("component", "graphql"),
            call.begin_subsegment().put_annotation(
                "query",
                "\n        subscription MySubscription {\n            onHi\n        }\n    ",  # noqa: E501
            ),
            call.end_subsegment(),
        ]
    )
    assert len(mock_xray_recorder.mock_calls) == 5
    mock_xray_recorder.begin_subsegment().add_exception.assert_called()


def test_datadog_tracer_sync(xray_extension_sync, mocker):
    extension, mock_xray_recorder = xray_extension_sync
    schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=[extension])

    query = """
        query {
            person {
                name
            }
        }
    """

    schema.execute_sync(query)

    assert mock_xray_recorder.mock_calls == [
        call.begin_subsegment(name="GraphQL Query"),
        call.begin_subsegment().put_annotation("component", "graphql"),
        call.begin_subsegment().put_annotation(
            "query",
            "\n        query {\n            person {\n                name\n            }\n        }\n    ",  # noqa: E501
        ),
        call.in_subsegment_async("GraphQL Resolving: person"),
        call.in_subsegment_async().__aenter__(),
        call.in_subsegment_async().__aenter__().put_annotation("component", "graphql"),
        call.in_subsegment_async()
        .__aenter__()
        .put_annotation("graphql_parentType", "Query"),
        call.in_subsegment_async()
        .__aenter__()
        .put_annotation("graphql_path", "person"),
        call.in_subsegment_async().__aexit__(None, None, None),
        call.end_subsegment(),
    ]


def test_uses_operation_name_and_hash_sync(xray_extension_sync):
    extension, mock_xray_recorder = xray_extension_sync

    schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=[extension])

    query = """
        query MyExampleQuery {
            person {
                name
            }
        }
    """

    schema.execute_sync(query, operation_name="MyExampleQuery")

    assert mock_xray_recorder.mock_calls == [
        call.begin_subsegment(name="GraphQL Query: MyExampleQuery"),
        call.begin_subsegment().put_annotation("component", "graphql"),
        call.begin_subsegment().put_annotation(
            "query",
            "\n        query MyExampleQuery {\n            person {\n                name\n            }\n        }\n    ",  # noqa: E501
        ),
        call.in_subsegment_async("GraphQL Resolving: person"),
        call.in_subsegment_async().__aenter__(),
        call.in_subsegment_async().__aenter__().put_annotation("component", "graphql"),
        call.in_subsegment_async()
        .__aenter__()
        .put_annotation("graphql_parentType", "Query"),
        call.in_subsegment_async()
        .__aenter__()
        .put_annotation("graphql_path", "person"),
        call.in_subsegment_async().__aexit__(None, None, None),
        call.end_subsegment(),
    ]


def test_uses_operation_type_sync(xray_extension_sync):
    extension, mock_xray_recorder = xray_extension_sync

    schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=[extension])

    query = """
        mutation MyMutation {
            sayHi
        }
    """

    schema.execute_sync(query, operation_name="MyMutation")

    assert mock_xray_recorder.mock_calls == [
        call.begin_subsegment(name="GraphQL Query: MyMutation"),
        call.begin_subsegment().put_annotation("component", "graphql"),
        call.begin_subsegment().put_annotation(
            "query",
            "\n        mutation MyMutation {\n            sayHi\n        }\n    ",
        ),
        call.in_subsegment_async("GraphQL Resolving: sayHi"),
        call.in_subsegment_async().__aenter__(),
        call.in_subsegment_async().__aenter__().put_annotation("component", "graphql"),
        call.in_subsegment_async()
        .__aenter__()
        .put_annotation("graphql_parentType", "Mutation"),
        call.in_subsegment_async().__aenter__().put_annotation("graphql_path", "sayHi"),
        call.in_subsegment_async().__aexit__(None, None, None),
        call.end_subsegment(),
    ]
