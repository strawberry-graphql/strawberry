from cached_property import cached_property
from graphql import GraphQLSchema
from graphql.subscription import subscribe

from strawberry.backends import StrawberryBackend
from .execute import execute, execute_sync


class GraphQLCoreBackend(StrawberryBackend):

    # TODO: Other parameters
    def execute(self, query: str) -> ...:
        return execute_sync(self.schema, query)

    # TODO: Other parameters
    async def execute_async(self, query: str) -> ...:
        return await execute(self.schema, query)

    # TODO: Other parameters
    async def subscribe(self, query: str) -> ...:
        # TODO: subscribe expects query to be a DocumentNode
        return await subscribe(self.schema, query)

    @cached_property
    def schema(self) -> GraphQLSchema:
        # TODO: Implement
        ...
