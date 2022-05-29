from dataclasses import dataclass
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from strawberry.channels.handlers.base import ChannelsConsumer


@dataclass
class StrawberryChannelsContext:
    """
    A Channels context for GraphQL
    """

    request: "ChannelsConsumer"

    @property
    def ws(self):
        return self.request

    def __getitem__(self, key):
        # __getitem__ override needed to avoid issues for who's
        # using info.context["request"]
        return super().__getattribute__(key)

    def get(self, key):
        """Enable .get notation for accessing the request"""
        return super().__getattribute__(key)
