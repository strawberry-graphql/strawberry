import strawberry
from flask import Flask
from strawberry.file_uploads import Upload
from strawberry.flask.views import GraphQLView as BaseGraphQLView


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

    app = Flask(__name__)
    app.debug = True

    app.add_url_rule(
        "/graphql",
        view_func=GraphQLView.as_view("graphql_view", schema=schema, **kwargs),
    )
    return app
