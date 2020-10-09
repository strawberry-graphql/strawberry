from typing import Optional

from graphql.subscription import subscribe

from strawberry.backends import StrawberryBackend
from strawberry.types import StrawberryObjectType
from .converter import GraphQLCoreConverter
from .execute import execute, execute_sync


class GraphQLCoreBackend(StrawberryBackend):

    def __init__(self, query: StrawberryObjectType,
                 mutation: Optional[StrawberryObjectType] = None,
                 subscription: Optional[StrawberryObjectType] = None):
        super().__init__(query, mutation, subscription)

        # TODO: I'm not a fan of this workflow. It would be better if we could
        #       somehow take the StrawberrySchema itself through the converter
        converter = GraphQLCoreConverter()
        self.schema = converter.to_schema(query, mutation, subscription)

    # TODO: Other parameters
    def execute_sync(self, query: str) -> ...:
        return execute_sync(self.schema, query)

    # TODO: Other parameters
    async def execute(self, query: str) -> ...:
        return await execute(self.schema, query)

    # TODO: Other parameters
    async def subscribe(self, query: str) -> ...:
        # TODO: subscribe expects query to be a DocumentNode
        return await subscribe(self.schema, query)
