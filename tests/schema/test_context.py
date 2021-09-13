import json

import pytest

from django.test.client import RequestFactory

import strawberry
from strawberry.django.views import GraphQLView


def test_context_access():
    @strawberry.type
    class Query:
        @strawberry.field
        def my_field(self) -> str:
            return strawberry.context["some_context"]

    schema = strawberry.Schema(Query)

    result = schema.execute_sync(
        "query { myField }",
        context_value={
            "some_context": "hi",
        },
    )

    assert not result.errors
    assert result.data == {
        "myField": "hi",
    }


def test_context_dot_access():
    def resolve_my_field():
        return strawberry.context.some_context

    @strawberry.type
    class Query:
        my_field: str = strawberry.field(resolver=resolve_my_field)

    schema = strawberry.Schema(Query)

    result = schema.execute_sync(
        "query { myField }",
        context_value={
            "some_context": "hi",
        },
    )

    assert not result.errors
    assert result.data == {
        "myField": "hi",
    }


def test_context_get_access():
    @strawberry.type
    class Query:
        @strawberry.field
        def my_field(self) -> str:
            return strawberry.context.get("some_context")

    schema = strawberry.Schema(Query)

    result = schema.execute_sync(
        "query { myField }",
        context_value={
            "some_context": "hi",
        },
    )

    assert not result.errors
    assert result.data == {
        "myField": "hi",
    }


def test_access_outside_of_execute_errors():
    with pytest.raises(Exception):
        strawberry.context["some_context"]


@pytest.mark.asyncio
async def test_async_access():
    @strawberry.type
    class Query:
        @strawberry.field
        async def my_field(self) -> str:
            return strawberry.context["some_context"]

    schema = strawberry.Schema(Query)

    result = await schema.execute(
        "query { myField }",
        context_value={
            "some_context": "hi",
        },
    )

    assert not result.errors
    assert result.data == {
        "myField": "hi",
    }


def test_context_access_with_django():
    factory = RequestFactory()

    @strawberry.type
    class Query:
        @strawberry.field
        def request_path(self) -> str:
            return strawberry.context["request"].path

    schema = strawberry.Schema(query=Query)

    query = "{ requestPath }"
    request = factory.post(
        "/graphql/", {"query": query}, content_type="application/json"
    )

    response = GraphQLView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())

    assert response.status_code == 200
    assert not data.get("errors")
    assert data["data"] == {"requestPath": "/graphql/"}
