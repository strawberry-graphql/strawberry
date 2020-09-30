import json
from typing import Optional

import pytest

from django.http import Http404
from django.test.client import RequestFactory

import strawberry
from strawberry.django.views import GraphQLView as BaseGraphQLView
from strawberry.permission import BasePermission
from strawberry.types import ExecutionResult

from .app.models import Example


class AlwaysFailPermission(BasePermission):
    message = "You are not authorized"

    def has_permission(self, source, info):
        return False


@strawberry.type
class Query:
    hello: str = "strawberry"

    @strawberry.field
    async def hello_async(self, info) -> str:
        return "async strawberry"

    @strawberry.field(permission_classes=[AlwaysFailPermission])
    def always_fail(self, info) -> Optional[str]:
        return "Hey"

    @strawberry.field
    async def example_async(self, info) -> str:
        return Example.objects.first().name

    @strawberry.field
    def example(self, info) -> str:
        return Example.objects.first().name


schema = strawberry.Schema(query=Query)


class GraphQLView(BaseGraphQLView):
    def get_root_value(self, request):
        return Query()


def test_graphiql_view():
    factory = RequestFactory()

    request = factory.get("/graphql/", HTTP_ACCEPT="text/html")

    response = GraphQLView.as_view(schema=schema)(request)
    body = response.content.decode()

    assert "GraphiQL" in body


def test_graphiql_disabled_view():
    factory = RequestFactory()

    request = factory.get("/graphql/", HTTP_ACCEPT="text/html")

    with pytest.raises(Http404):
        GraphQLView.as_view(schema=schema, graphiql=False)(request)


def test_graphql_query():
    query = "{ hello }"

    factory = RequestFactory()
    request = factory.post(
        "/graphql/", {"query": query}, content_type="application/json"
    )

    response = GraphQLView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())

    assert data["data"]["hello"] == "strawberry"


@pytest.mark.django_db
def test_graphql_query_model():
    Example.objects.create(name="This is a demo")

    query = "{ example }"

    factory = RequestFactory()
    request = factory.post(
        "/graphql/", {"query": query}, content_type="application/json"
    )

    response = GraphQLView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())

    assert not data.get("errors")
    assert data["data"]["example"] == "This is a demo"


@pytest.mark.xfail(reason="We don't support async on django at the moment")
def test_async_graphql_query():
    query = "{ helloAsync }"

    factory = RequestFactory()
    request = factory.post(
        "/graphql/", {"query": query}, content_type="application/json"
    )

    response = GraphQLView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())

    assert data["data"]["helloAsync"] == "async strawberry"


@pytest.mark.xfail(reason="We don't support async on django at the moment")
def test_async_graphql_query_model():
    Example.objects.create(name="This is a demo async")

    query = "{ exampleAsync }"

    factory = RequestFactory()
    request = factory.post(
        "/graphql/", {"query": query}, content_type="application/json"
    )

    response = GraphQLView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())

    assert data["data"]["exampleAsync"] == "This is a demo async"


def test_returns_errors_and_data():
    query = "{ hello, alwaysFail }"

    factory = RequestFactory()
    request = factory.post(
        "/graphql/", {"query": query}, content_type="application/json"
    )

    response = GraphQLView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())

    assert response.status_code == 200

    assert data["data"]["hello"] == "strawberry"
    assert data["data"]["alwaysFail"] is None

    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == "You are not authorized"


def test_custom_context():
    class CustomGraphQLView(BaseGraphQLView):
        def get_context(self, request):
            return {
                "request": request,
                "custom_value": "Hi!",
            }

    factory = RequestFactory()

    @strawberry.type
    class Query:
        @strawberry.field
        def custom_context_value(self, info) -> str:
            return info.context["custom_value"]

    schema = strawberry.Schema(query=Query)

    query = "{ customContextValue }"
    request = factory.post(
        "/graphql/", {"query": query}, content_type="application/json"
    )

    response = CustomGraphQLView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())

    assert response.status_code == 200
    assert data["data"] == {"customContextValue": "Hi!"}


def test_custom_process_result():
    class CustomGraphQLView(BaseGraphQLView):
        def process_result(self, request, result: ExecutionResult):
            return {}

    factory = RequestFactory()

    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info) -> str:
            return "ABC"

    schema = strawberry.Schema(query=Query)

    query = "{ abc }"
    request = factory.post(
        "/graphql/", {"query": query}, content_type="application/json"
    )

    response = CustomGraphQLView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())

    assert response.status_code == 200
    assert data == {}
