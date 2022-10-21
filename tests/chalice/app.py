from typing import Any, Optional

import strawberry
from chalice import Chalice  # type: ignore
from strawberry.chalice.views import GraphQLView
from strawberry.types.info import Info


app = Chalice(app_name="TheStackBadger")


@strawberry.type
class Query:
    @strawberry.field
    def greetings(self) -> str:
        return "hello"

    @strawberry.field
    def hello(self, name: Optional[str] = None) -> str:
        return f"Hello {name or 'world'}"

    @strawberry.field
    def teapot(self, info: Info[Any, None]) -> str:
        info.context["response"].status_code = 418

        return "🫖"


@strawberry.type
class Mutation:
    @strawberry.mutation
    def echo(self, string_to_echo: str) -> str:
        return string_to_echo


schema = strawberry.Schema(query=Query, mutation=Mutation)
view = GraphQLView(schema=schema, graphiql=True)
view_no_graphiql = GraphQLView(schema=schema, graphiql=False)


@app.route("/")
def index():
    return {"strawberry": "cake"}


@app.route("/graphql", methods=["GET", "POST"], content_types=["application/json"])
def handle_graphql():
    return view.execute_request(app.current_request)


@app.route(
    "/graphql-no-graphiql",
    methods=["GET", "POST", "PUT"],
    content_types=["application/json"],
)
def handle_graphql_without_graphiql():
    return view_no_graphiql.execute_request(app.current_request)
