import json
from typing import Any, Optional

import pytest

from django.test.client import RequestFactory

import strawberry
from strawberry.django.views import GraphQLView as BaseGraphQLView
from strawberry.permission import BasePermission
from strawberry.types import ExecutionResult, Info

from .app.models import Example


class AlwaysFailPermission(BasePermission):
    message = "You are not authorized"

    def has_permission(self, source: Any, info: Info, **kwargs) -> bool:
        return False


@strawberry.type
class Query:
    hello: str = "strawberry"

    @strawberry.field
    def hi(self, name: Optional[str] = None) -> str:
        return f"Hello {name or 'world'}"

    @strawberry.field(permission_classes=[AlwaysFailPermission])
    def always_fail(self) -> Optional[str]:
        return "Hey"

    @strawberry.field
    def example(self) -> str:
        return Example.objects.first().name


@strawberry.type
class GetRequestValueWithDotNotationQuery:
    @strawberry.field
    def get_request_value(self, info: Info) -> str:
        return info.context.request


@strawberry.type
class GetRequestValueUsingGetQuery:
    @strawberry.field
    def get_request_value(self, info: Info) -> str:
        return info.context.get("request")


@strawberry.type
class GetRequestValueQuery:
    @strawberry.field
    def get_request_value(self, info: Info) -> str:
        return info.context["request"]


schema = strawberry.Schema(query=Query)


class GraphQLView(BaseGraphQLView):
    def get_root_value(self, request):
        return Query()


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

    Example.objects.all().delete()


def test_custom_process_result():
    class CustomGraphQLView(BaseGraphQLView):
        def process_result(self, request, result: ExecutionResult):
            return {}

    factory = RequestFactory()

    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self) -> str:
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


def test_can_set_cookies():
    factory = RequestFactory()

    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info: Info) -> str:
            info.context.response.set_cookie("fruit", "strawberry")

            return "ABC"

    schema = strawberry.Schema(query=Query)

    query = "{ abc }"
    request = factory.post(
        "/graphql/", {"query": query}, content_type="application/json"
    )

    response = GraphQLView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())

    assert response.status_code == 200
    assert response.cookies["fruit"].value == "strawberry"
    assert data == {"data": {"abc": "ABC"}}


def test_can_set_headers():
    factory = RequestFactory()

    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info: Info) -> str:
            info.context.response["My-Header"] = "header value"

            return "ABC"

    schema = strawberry.Schema(query=Query)

    query = "{ abc }"
    request = factory.post(
        "/graphql/", {"query": query}, content_type="application/json"
    )

    response = GraphQLView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())

    assert response.status_code == 200
    assert response["my-header"] == "header value"
    assert data == {"data": {"abc": "ABC"}}


def test_can_change_status_code():
    factory = RequestFactory()

    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info: Info) -> str:
            info.context.response.status_code = 418

            return "ABC"

    schema = strawberry.Schema(query=Query)

    query = "{ abc }"
    request = factory.post(
        "/graphql/", {"query": query}, content_type="application/json"
    )

    response = GraphQLView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())

    assert response.status_code == 418
    assert data == {"data": {"abc": "ABC"}}


def test_json_encoder():
    query = "{ hello }"

    factory = RequestFactory()
    request = factory.post(
        "/graphql/", {"query": query}, content_type="application/json"
    )

    class CustomEncoder(json.JSONEncoder):
        def encode(self, o: Any) -> str:
            # Reverse the result.
            return super().encode(o)[::-1]

    response1 = GraphQLView.as_view(schema=schema, json_encoder=CustomEncoder)(request)
    assert response1.content.decode() == '{"data": {"hello": "strawberry"}}'[::-1]

    class CustomGraphQLView(GraphQLView):
        json_encoder = CustomEncoder

    response2 = CustomGraphQLView.as_view(schema=schema)(request)
    assert response1.content == response2.content


def test_json_dumps_params():
    query = "{ hello }"

    factory = RequestFactory()
    request = factory.post(
        "/graphql/", {"query": query}, content_type="application/json"
    )

    dumps_params = {"separators": (",", ":")}

    response1 = GraphQLView.as_view(schema=schema, json_dumps_params=dumps_params)(
        request
    )
    assert response1.content.decode() == '{"data":{"hello":"strawberry"}}'

    class CustomGraphQLView(GraphQLView):
        json_dumps_params = dumps_params

    response2 = CustomGraphQLView.as_view(schema=schema)(request)
    assert response1.content == response2.content
