from chalice import Chalice  # type: ignore
from strawberry.chalice.views import GraphQLView
from tests.views.schema import schema

app = Chalice(app_name="TheStackBadger")


view = GraphQLView(schema=schema, graphiql=True, allow_queries_via_get=True)
view_no_graphiql = GraphQLView(schema=schema, graphiql=False)
view_not_get = GraphQLView(schema=schema, graphiql=False, allow_queries_via_get=False)


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


@app.route(
    "/graphql-no-get",
    methods=["GET", "POST", "PUT"],
    content_types=["application/json"],
)
def handle_graphql_without_queries_via_get():
    return view_not_get.execute_request(app.current_request)
