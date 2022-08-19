import strawberry
from aiohttp import hdrs, web
from strawberry.aiohttp.views import GraphQLView
from strawberry.types import ExecutionResult, Info


async def test_graphql_query(graphql_client):
    query = """
        query ($name: String) {
            hello(name: $name)
        }
    """

    response = await graphql_client.query(query=query, variables={"name": "strawberry"})

    assert response.data["hello"] == "Hello strawberry"


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


async def test_malformed_query(graphql_client):
    query = """
        qwary {
            hello
        }
    """

    response = await graphql_client.query(query=query, asserts_errors=False)

    assert response.errors[0]["message"] == "Syntax Error: Unexpected Name 'qwary'."


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


async def test_operation_selection(aiohttp_app_client):
    query = {
        "query": """
            query Operation1 {
                hello(name: "Operation1")
            }
            query Operation2 {
                hello(name: "Operation2")
            }
        """,
        "operationName": "Operation2",
    }

    response = await aiohttp_app_client.post("/graphql", json=query)
    data = await response.json()
    assert response.status == 200
    assert data["data"]["hello"] == "Hello Operation2"
