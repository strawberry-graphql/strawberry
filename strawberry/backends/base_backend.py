from abc import ABC, abstractmethod
from typing import Optional, Type

from strawberry.types import StrawberryObjectType


class StrawberryBackend(ABC):

    def __init__(self, query: Type[StrawberryObjectType],
                 mutation: Optional[Type[StrawberryObjectType]] = None,
                 subscription: Optional[Type[StrawberryObjectType]] = None):
        self.query = query
        self.mutation = mutation
        self.subscription = subscription

    # TODO: Other parameters
    @abstractmethod
    def execute(self, query: str) -> ...:
        # TODO: Rename query to document?
        ...

    # TODO: Other parameters
    @abstractmethod
    async def execute_async(self, query: str) -> ...:
        ...

    # TODO: Other parameters
    @abstractmethod
    async def subscribe(self, query: str) -> ...:
        # TODO: Should you be able to make subscription queries from execute and
        #       execute_async?
        # TODO: Should there be a subscribe/subscribe_async combo?
        ...
