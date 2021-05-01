from random import random

import strawberry
from sanic import Sanic
from strawberry.file_uploads import Upload
from strawberry.sanic.views import GraphQLView as BaseGraphQLView


def create_app(**kwargs):
    @strawberry.type
    class Query:
        hello: str = "strawberry"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def read_text(self, text_file: Upload) -> str:
            return text_file.read().decode()

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    class GraphQLView(BaseGraphQLView):
        def get_root_value(self):
            return Query()

    app = Sanic("test-app-" + str(random()))

    app.add_route(
        GraphQLView.as_view(schema=schema, graphiql=kwargs.get("graphiql", True)),
        "/graphql",
    )
    return app
