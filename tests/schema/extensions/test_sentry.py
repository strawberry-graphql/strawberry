from typing import AsyncGenerator

import pytest

import strawberry


@pytest.fixture
def sentry_extension(mocker):
    sentry_mock = mocker.MagicMock()

    mocker.patch.dict("sys.modules", sentry_sdk=sentry_mock)

    from strawberry.extensions.tracing.sentry import SentryTracingExtension

    return SentryTracingExtension, sentry_mock


@pytest.fixture
def sentry_extension_sync(mocker):
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
async def test_sentry_tracer(sentry_extension, mocker):
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

    await schema.execute(query)

    mock.start_transaction.assert_has_calls(
        [
            mocker.call(op="gql", name="Anonymous Query"),
            mocker.call().set_tag("graphql.operation_type", "query"),
            mocker.call().start_child(op="parsing", description="Parsing"),
            mocker.call().start_child().finish(),
            mocker.call().start_child(op="validation", description="Validation"),
            mocker.call().start_child().finish(),
            mocker.call().start_child(
                op="resolve", description="Resolving: Query.personAsync"
            ),
            mocker.call().start_child().__enter__(),
            mocker.call()
            .start_child()
            .__enter__()
            .set_tag("graphql.field_name", "personAsync"),
            mocker.call()
            .start_child()
            .__enter__()
            .set_tag("graphql.parent_type", "Query"),
            mocker.call()
            .start_child()
            .__enter__()
            .set_tag("graphql.field_path", "Query.personAsync"),
            mocker.call()
            .start_child()
            .__enter__()
            .set_tag("graphql.path", "personAsync"),
            mocker.call().start_child().__exit__(None, None, None),
            mocker.call().finish(),
        ]
    )


@pytest.mark.asyncio
async def test_uses_operation_name(sentry_extension):
    extension, mock = sentry_extension

    schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=[extension])

    query = """
        query MyExampleQuery {
            person {
                name
            }
        }
    """

    await schema.execute(query, operation_name="MyExampleQuery")

    mock.start_transaction.assert_any_call(op="gql", name="MyExampleQuery")


@pytest.mark.asyncio
async def test_uses_operation_type(sentry_extension):
    extension, mock = sentry_extension

    schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=[extension])

    query = """
        mutation MyMutation {
            sayHi
        }
    """

    await schema.execute(query, operation_name="MyMutation")
    mock.start_transaction().set_tag.assert_any_call(
        "graphql.operation_type", "mutation"
    )


@pytest.mark.asyncio
async def test_uses_operation_subscription(sentry_extension):
    extension, mock = sentry_extension

    schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=[extension])

    query = """
        subscription MySubscription {
            onHi
        }
    """

    await schema.execute(query, operation_name="MySubscription")
    mock.start_transaction().set_tag.assert_any_call(
        "graphql.operation_type", "subscription"
    )


def test_sentry_tracer_sync(sentry_extension_sync, mocker):
    extension, mock = sentry_extension_sync
    schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=[extension])

    query = """
        query {
            person {
                name
            }
        }
    """

    schema.execute_sync(query)

    mock.start_transaction.assert_has_calls(
        [
            mocker.call(op="gql", name="Anonymous Query"),
            mocker.call().set_tag("graphql.operation_type", "query"),
            mocker.call().start_child(op="parsing", description="Parsing"),
            mocker.call().start_child().finish(),
            mocker.call().start_child(op="validation", description="Validation"),
            mocker.call().start_child().finish(),
            mocker.call().start_child(
                op="resolve", description="Resolving: Query.person"
            ),
            mocker.call().start_child().__enter__(),
            mocker.call()
            .start_child()
            .__enter__()
            .set_tag("graphql.field_name", "person"),
            mocker.call()
            .start_child()
            .__enter__()
            .set_tag("graphql.parent_type", "Query"),
            mocker.call()
            .start_child()
            .__enter__()
            .set_tag("graphql.field_path", "Query.person"),
            mocker.call().start_child().__enter__().set_tag("graphql.path", "person"),
            mocker.call().start_child().__exit__(None, None, None),
            mocker.call().finish(),
        ]
    )


def test_uses_operation_name__sync(sentry_extension_sync):
    extension, mock = sentry_extension_sync

    schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=[extension])

    query = """
        query MyExampleQuery {
            person {
                name
            }
        }
    """

    schema.execute_sync(query, operation_name="MyExampleQuery")

    mock.start_transaction.assert_any_call(op="gql", name="MyExampleQuery")


def test_uses_operation_type_sync(sentry_extension_sync):
    extension, mock = sentry_extension_sync

    schema = strawberry.Schema(query=Query, mutation=Mutation, extensions=[extension])

    query = """
        mutation MyMutation {
            sayHi
        }
    """

    schema.execute_sync(query, operation_name="MyMutation")

    mock.start_transaction().set_tag.assert_any_call(
        "graphql.operation_type", "mutation"
    )
