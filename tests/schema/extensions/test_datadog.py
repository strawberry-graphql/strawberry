from typing import AsyncGenerator

import pytest

import strawberry


@pytest.fixture
def datadog_extension(mocker):
    datadog_mock = mocker.MagicMock()

    mocker.patch.dict("sys.modules", ddtrace=datadog_mock)

    from strawberry.extensions.tracing.datadog import DatadogTracingExtension

    return DatadogTracingExtension, datadog_mock


@pytest.fixture
def datadog_extension_sync(mocker):
    datadog_mock = mocker.MagicMock()

    mocker.patch.dict("sys.modules", ddtrace=datadog_mock)

    from strawberry.extensions.tracing.datadog import DatadogTracingExtensionSync

    return DatadogTracingExtensionSync, datadog_mock


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
async def test_datadog_tracer(datadog_extension, mocker):
    extension, mock = datadog_extension

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

    mock.tracer.assert_has_calls(
        [
            mocker.call.trace(
                "Anonymous Query",
                resource="63a280256ca4e8514e06cf90b30c8c3a",
                span_type="graphql",
                service="strawberry",
            ),
            mocker.call.trace().set_tag("graphql.operation_name", None),
            mocker.call.trace().set_tag("graphql.operation_type", "query"),
            mocker.call.trace("Parsing", span_type="graphql"),
            mocker.call.trace().finish(),
            mocker.call.trace("Validation", span_type="graphql"),
            mocker.call.trace().finish(),
            mocker.call.trace("Resolving: Query.personAsync", span_type="graphql"),
            mocker.call.trace().__enter__(),
            mocker.call.trace()
            .__enter__()
            .set_tag("graphql.field_name", "personAsync"),
            mocker.call.trace().__enter__().set_tag("graphql.parent_type", "Query"),
            mocker.call.trace()
            .__enter__()
            .set_tag("graphql.field_path", "Query.personAsync"),
            mocker.call.trace().__enter__().set_tag("graphql.path", "personAsync"),
            mocker.call.trace().__exit__(None, None, None),
            mocker.call.trace().finish(),
        ]
    )


@pytest.mark.asyncio
async def test_uses_operation_name_and_hash(datadog_extension):
    extension, mock = datadog_extension

    schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=[extension])

    query = """
        query MyExampleQuery {
            person {
                name
            }
        }
    """

    await schema.execute(query, operation_name="MyExampleQuery")

    mock.tracer.trace.assert_any_call(
        "MyExampleQuery",
        resource="MyExampleQuery:efe8d7247ee8136f45e3824c2768b155",
        span_type="graphql",
        service="strawberry",
    )


@pytest.mark.asyncio
async def test_uses_operation_type(datadog_extension):
    extension, mock = datadog_extension

    schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=[extension])

    query = """
        mutation MyMutation {
            sayHi
        }
    """

    await schema.execute(query, operation_name="MyMutation")
    mock.tracer.trace().set_tag.assert_any_call("graphql.operation_type", "mutation"),


@pytest.mark.asyncio
async def test_uses_operation_subscription(datadog_extension):
    extension, mock = datadog_extension

    schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=[extension])

    query = """
        subscription MySubscription {
            onHi
        }
    """

    await schema.execute(query, operation_name="MySubscription")
    mock.tracer.trace().set_tag.assert_any_call(
        "graphql.operation_type", "subscription"
    ),


def test_datadog_tracer_sync(datadog_extension_sync, mocker):
    extension, mock = datadog_extension_sync
    schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=[extension])

    query = """
        query {
            person {
                name
            }
        }
    """

    schema.execute_sync(query)

    mock.tracer.assert_has_calls(
        [
            mocker.call.trace(
                "Anonymous Query",
                resource="659edba9e6ac9c20d03da1b2d0f9a956",
                span_type="graphql",
                service="strawberry",
            ),
            mocker.call.trace().set_tag("graphql.operation_name", None),
            mocker.call.trace().set_tag("graphql.operation_type", "query"),
            mocker.call.trace("Parsing", span_type="graphql"),
            mocker.call.trace().finish(),
            mocker.call.trace("Validation", span_type="graphql"),
            mocker.call.trace().finish(),
            mocker.call.trace("Resolving: Query.person", span_type="graphql"),
            mocker.call.trace().__enter__(),
            mocker.call.trace().__enter__().set_tag("graphql.field_name", "person"),
            mocker.call.trace().__enter__().set_tag("graphql.parent_type", "Query"),
            mocker.call.trace()
            .__enter__()
            .set_tag("graphql.field_path", "Query.person"),
            mocker.call.trace().__enter__().set_tag("graphql.path", "person"),
            mocker.call.trace().__exit__(None, None, None),
            mocker.call.trace().finish(),
        ]
    )


def test_uses_operation_name_and_hash_sync(datadog_extension_sync):
    extension, mock = datadog_extension_sync

    schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=[extension])

    query = """
        query MyExampleQuery {
            person {
                name
            }
        }
    """

    schema.execute_sync(query, operation_name="MyExampleQuery")

    mock.tracer.trace.assert_any_call(
        "MyExampleQuery",
        resource="MyExampleQuery:efe8d7247ee8136f45e3824c2768b155",
        span_type="graphql",
        service="strawberry",
    )


def test_uses_operation_type_sync(datadog_extension_sync):
    extension, mock = datadog_extension_sync

    schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=[extension])

    query = """
        mutation MyMutation {
            sayHi
        }
    """

    schema.execute_sync(query, operation_name="MyMutation")

    mock.tracer.trace().set_tag.assert_any_call("graphql.operation_type", "mutation"),
