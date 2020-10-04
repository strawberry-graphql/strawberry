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

    @abstractmethod
    def execute(self, query: str) -> ...:
        # TODO: Rename query to document?
        ...

    @abstractmethod
    async def execute_async(self, query: str) -> ...:
        ...

    @abstractmethod
    async def subscribe(self, query: str) -> ...:
        ...
