import aiohttp.web
import strawberry
from strawberry.aiohttp.views import GraphQLView as BaseGraphQLView
from strawberry.file_uploads import Upload


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
        async def get_root_value(self):
            return Query()

    app = aiohttp.web.Application()
    app.router.add_view("/graphql", GraphQLView.as_view(schema=schema, **kwargs))

    return app
