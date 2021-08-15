import strawberry
from chalice import Chalice  # type: ignore
from chalice.app import Request
from strawberry.chalice.views import GraphQLView


app = Chalice(app_name="TheStackBadger")


@strawberry.type
class Query:
    @strawberry.field
    def greetings(self) -> str:
        return "hello"


@strawberry.type
class Mutation:
    @strawberry.mutation
    def echo(self, string_to_echo: str) -> str:
        return string_to_echo


schema = strawberry.Schema(query=Query, mutation=Mutation)
view = GraphQLView(schema=schema, render_graphiql=True)


@app.route("/")
def index():
    return {"strawberry": "cake"}


@app.route("/graphql", methods=["GET", "POST"], content_types=["application/json"])
def handle_graphql():
    request: Request = app.current_request
    result = view.execute_request(request)
    return result
