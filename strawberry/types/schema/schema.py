from typing import Optional, Set, Type

from cached_property import cached_property

from strawberry.backends import GraphQLCoreBackend, StrawberryBackend
from strawberry.types import StrawberryObjectType, StrawberryType


class StrawberrySchema:
    def __init__(self, query: StrawberryObjectType, *,
                 mutation: Optional[StrawberryObjectType] = None,
                 subscription: Optional[StrawberryObjectType] = None,
                 backend: Type[StrawberryBackend] = GraphQLCoreBackend):
        self.backend = backend(query, mutation, subscription)

    # TODO: Implement
    def __repr__(self) -> str:
        ...

    # TODO: Implement
    # This replaces the old to_str method
    def __str__(self) -> str:
        ...

    # TODO: Other args
    # TODO: Return type
    async def execute(self, query: str) -> ...:
        return await self.backend.execute(query)

    # TODO: Other args
    # TODO: Return type
    def execute_sync(self, query: str) -> ...:
        return self.backend.execute_sync(query)

    @cached_property
    def types(self) -> Set[StrawberryType]:
        # TODO: Implement
        ...
