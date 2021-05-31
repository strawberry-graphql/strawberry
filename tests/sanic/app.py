import typing
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

        @strawberry.mutation
        def read_files(self, files: typing.List[Upload]) -> typing.List[str]:
            contents = []
            for file in files:
                contents.append(file.read().decode())
            return contents

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    class GraphQLView(BaseGraphQLView):
        def get_root_value(self):
            return Query()

    app = Sanic(f"test-app-{random()}")

    app.add_route(
        GraphQLView.as_view(schema=schema, graphiql=kwargs.get("graphiql", True)),
        "/graphql",
    )
    return app
