from starlette.applications import Starlette
from strawberry.contrib.starlette.app.graphql_app import GraphQLApp


def get_graphql_app(schema, tracing=False):
    app = Starlette(debug=True)
    app.add_route("/graphql", GraphQLApp(schema, tracing=tracing))
    return app


def create_query(query, variables=None, operation_name=None):
    return {"query": query, "variables": variables, "operationName": operation_name}
