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

    # TODO: I switched from execute_sync to execute_async as that appears to be
    #       the standard for async "overloads". Certainly up for discussion;
    #       leaning on switching it back
    #       https://stackoverflow.com/q/52459138/8134178
    def execute(self, query: str):
        return self.backend.execute(query)

    async def execute_async(self, query: str):
        return await self.backend.execute_async(query)

    @cached_property
    def types(self) -> Set[StrawberryType]:
        ...

    # TODO: Should this just be __str__?
    def as_str(self) -> str:
        ...
