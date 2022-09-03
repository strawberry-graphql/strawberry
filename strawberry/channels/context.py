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
