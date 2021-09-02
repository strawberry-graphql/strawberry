import strawberry
from aiohttp import hdrs, web
from strawberry.aiohttp.views import GraphQLView
from strawberry.types import ExecutionResult, Info

from .app import create_app


async def test_graphql_query(aiohttp_app_client):
    query = {
        "query": """
            query {
                hello
            }
        """
    }

    response = await aiohttp_app_client.post("/graphql", json=query)
    data = await response.json()
    assert response.status == 200
    assert data["data"]["hello"] == "strawberry"


async def test_graphiql_view(aiohttp_app_client):
    response = await aiohttp_app_client.get("/graphql", headers={"Accept": "text/html"})
    body = await response.text()

    assert "GraphiQL" in body


async def test_graphiql_disabled_view(aiohttp_client):
    app = create_app(graphiql=False)
    client = await aiohttp_client(app)

    response = await client.get("/graphql", headers={"Accept": "text/html"})
    assert response.status == 404


async def test_custom_context(aiohttp_client):
    class CustomGraphQLView(GraphQLView):
        async def get_context(self, request: web.Request, response: web.StreamResponse):
            return {"request": request, "response": response, "custom_value": "Hi!"}

    @strawberry.type
    class Query:
        @strawberry.field
        def custom_context_value(self, info: Info) -> str:
            return info.context["custom_value"]

    schema = strawberry.Schema(query=Query)

    app = web.Application()
    app.router.add_route("*", "/graphql", CustomGraphQLView(schema=schema))
    client = await aiohttp_client(app)

    query = "{ customContextValue }"
    resp = await client.post("/graphql", json={"query": query})
    data = await resp.json()

    assert resp.status == 200
    assert data["data"] == {"customContextValue": "Hi!"}


async def test_custom_process_result(aiohttp_client):
    class CustomGraphQLView(GraphQLView):
        async def process_result(self, request: web.Request, result: ExecutionResult):
            return {}

    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self) -> str:
            return "ABC"

    schema = strawberry.Schema(query=Query)

    app = web.Application()
    app.router.add_route("*", "/graphql", CustomGraphQLView(schema=schema))
    client = await aiohttp_client(app)

    query = "{ abc }"
    response = await client.post("/graphql", json={"query": query})
    data = await response.json()

    assert response.status == 200
    assert data == {}


async def test_setting_cookies_via_context(aiohttp_client):
    @strawberry.type
    class Query:
        @strawberry.field
        def abc(self, info) -> str:
            info.context["response"].set_cookie("TEST_COOKIE", "TEST_VALUE")
            return "ABC"

    schema = strawberry.Schema(query=Query)

    app = web.Application()
    app.router.add_route("*", "/graphql", GraphQLView(schema=schema))
    client = await aiohttp_client(app)

    query = "{ abc }"
    response = await client.post("/graphql", json={"query": query})

    assert response.status == 200
    assert response.cookies.get("TEST_COOKIE").value == "TEST_VALUE"


async def test_malformed_query(aiohttp_app_client):
    query = {
        "qwary": """
            qwary {
                hello
            }
        """
    }

    response = await aiohttp_app_client.post("/graphql", json=query)
    reason = await response.text()

    assert response.status == 400
    assert reason == "400: No GraphQL query found in the request"


async def test_sending_invalid_json_body(aiohttp_app_client):
    query = "}"

    response = await aiohttp_app_client.post(
        "/graphql", data=query, headers={"content-type": "application/json"}
    )
    reason = await response.text()

    assert response.status == 400
    assert reason == "400: Unable to parse request body as JSON"


async def test_not_allowed_methods(aiohttp_app_client):
    # The CONNECT method is not allowed, but would require SSL to be tested.
    not_allowed_methods = hdrs.METH_ALL.difference(
        {hdrs.METH_GET, hdrs.METH_POST, hdrs.METH_CONNECT}
    )

    for method in not_allowed_methods:
        response = await aiohttp_app_client.request(method, "/graphql")
        assert response.status == 405, method
