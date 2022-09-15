import json
from typing import Any, Optional

import pytest

from django.core.exceptions import BadRequest, SuspiciousOperation
from django.http import Http404, JsonResponse
from django.test.client import RequestFactory
from django.utils.http import urlencode

import strawberry
from strawberry.django.views import GraphQLView as BaseGraphQLView, TemporalHttpResponse
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


def test_graphiql_view():
    factory = RequestFactory()

    request = factory.get("/graphql/", HTTP_ACCEPT="text/html")

    response = GraphQLView.as_view(schema=schema)(request)
    body = response.content.decode()

    assert "GraphiQL" in body


@pytest.mark.parametrize("method", ["DELETE", "HEAD", "PUT", "PATCH"])
def test_disabled_methods(method):
    factory = RequestFactory()

    rf = getattr(factory, method.lower())

    request = rf("/graphql/")

    response = GraphQLView.as_view(schema=schema, graphiql=False)(request)

    assert response.status_code == 405


def test_fails_when_not_sending_query():
    factory = RequestFactory()

    request = factory.post("/graphql/")

    with pytest.raises(SuspiciousOperation) as e:
        GraphQLView.as_view(schema=schema, graphiql=False)(request)

    assert e.value.args == ("No GraphQL query found in the request",)


def test_fails_when_request_body_has_invalid_json():
    factory = RequestFactory()

    request = factory.post(
        "/graphql/", "definitely-not-json-string", content_type="application/json"
    )

    with pytest.raises(SuspiciousOperation) as e:
        GraphQLView.as_view(schema=schema, graphiql=False)(request)

    assert e.value.args == ("Unable to parse request body as JSON",)


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

    assert response["content-type"] == "application/json"
    assert data["data"]["hello"] == "strawberry"


def test_graphql_can_pass_variables():
    query = "query Hi($name: String!) { hi(name: $name) }"
    variables = {"name": "James"}

    factory = RequestFactory()
    request = factory.post(
        "/graphql/",
        {"query": query, "variables": variables},
        content_type="application/json",
    )

    response = GraphQLView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())

    assert response["content-type"] == "application/json"
    assert data["data"]["hi"] == "Hello James"


def test_graphql_get_query_using_params():
    params = {"query": "{ hello }"}

    factory = RequestFactory()
    request = factory.get(
        "/graphql",
        data=params,
    )

    response = GraphQLView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())

    assert data["data"]["hello"] == "strawberry"


def test_graphql_can_pass_variables_using_params():
    params = {
        "query": "query Hi($name: String!) { hi(name: $name) }",
        "variables": '{"name": "James"}',
    }

    factory = RequestFactory()
    request = factory.get(
        "/graphql",
        data=params,
    )

    response = GraphQLView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())

    assert data["data"]["hi"] == "Hello James"


def test_graphql_post_query_fails_using_params():
    params = {"query": "{ hello }"}

    factory = RequestFactory()
    request = factory.post(
        "/graphql",
        **{"QUERY_STRING": urlencode(params, doseq=True)},
        content_type="application/x-www-form-urlencoded",
    )

    with pytest.raises(SuspiciousOperation) as e:
        GraphQLView.as_view(schema=schema)(request)

    assert e.value.args == ("No GraphQL query found in the request",)


def test_graphql_get_does_not_allow_mutation():
    params = {"query": "mutation { hello }"}

    factory = RequestFactory()
    request = factory.get(
        "/graphql",
        data=params,
    )

    with pytest.raises(BadRequest, match="mutations are not allowed when using GET"):
        GraphQLView.as_view(schema=schema)(request)


def test_graphql_get_does_get_when_disabled():
    params = {"query": "{ hell }"}

    factory = RequestFactory()
    request = factory.get(
        "/graphql",
        data=params,
    )

    with pytest.raises(BadRequest, match="queries are not allowed when using GET"):
        GraphQLView.as_view(schema=schema, allow_queries_via_get=False)(request)


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


@pytest.mark.parametrize(
    "query",
    (
        GetRequestValueWithDotNotationQuery,
        GetRequestValueUsingGetQuery,
        GetRequestValueQuery,
    ),
)
def test_strawberry_django_context(query):
    factory = RequestFactory()

    schema = strawberry.Schema(query=query)

    query = "{ getRequestValue }"
    request = factory.post(
        "/graphql/", {"query": query}, content_type="application/json"
    )

    response = GraphQLView.as_view(schema=schema)(request)
    data = json.loads(response.content.decode())
    assert response.status_code == 200
    assert data["data"] == {"getRequestValue": "<WSGIRequest: POST '/graphql/'>"}


def test_custom_context():
    class CustomGraphQLView(BaseGraphQLView):
        def get_context(self, request, response):
            return {"request": request, "custom_value": "Hi!"}

    factory = RequestFactory()

    @strawberry.type
    class Query:
        @strawberry.field
        def custom_context_value(self, info: Info) -> str:
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


def test_TemporalHttpResponse() -> None:
    resp = TemporalHttpResponse()
    assert repr(resp) == '<TemporalHttpResponse status_code=None, "application/json">'

    # Check that `__repr__` matches Django's output.
    resp.status_code = 200
    repr1 = repr(resp).replace("TemporalHttpResponse", "JsonResponse")
    assert repr1 == repr(JsonResponse({}))
