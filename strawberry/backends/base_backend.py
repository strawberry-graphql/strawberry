from abc import ABC, abstractmethod
from typing import Optional

from strawberry.types import StrawberryObjectType


class StrawberryBackend(ABC):

    def __init__(self, query: StrawberryObjectType,
                 mutation: Optional[StrawberryObjectType] = None,
                 subscription: Optional[StrawberryObjectType] = None):
        self.query = query
        self.mutation = mutation
        self.subscription = subscription

    # TODO: Other parameters
    @abstractmethod
    async def execute(self, query: str) -> ...:
        # TODO: Rename query to document?
        ...

    # TODO: Other parameters
    @abstractmethod
    def execute_sync(self, query: str) -> ...:
        ...

    # TODO: Other parameters
    @abstractmethod
    async def subscribe(self, query: str) -> ...:
        ...
