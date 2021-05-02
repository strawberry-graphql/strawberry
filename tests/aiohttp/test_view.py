import strawberry
from aiohttp import web
from strawberry.aiohttp.views import GraphQLView as BaseGraphQLView
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
    class CustomGraphQLView(BaseGraphQLView):
        async def get_context(self, request: web.Request):
            return {"request": request, "custom_value": "Hi!"}

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
    response = await client.post("/graphql", json={"query": query})
    data = await response.json()

    assert response.status == 200
    assert data["data"] == {"customContextValue": "Hi!"}


async def test_custom_process_result(aiohttp_client):
    class CustomGraphQLView(BaseGraphQLView):
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


async def test_malformed_query(aiohttp_app_client):
    query = {
        "qwary": """
            qwary {
                hello
            }
        """
    }

    response = await aiohttp_app_client.post("/graphql", json=query)
    assert response.status == 400
