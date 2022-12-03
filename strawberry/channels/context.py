from dataclasses import dataclass
from typing import Any, TYPE_CHECKING


if TYPE_CHECKING:
    from strawberry.channels.handlers.base import ChannelsConsumer


@dataclass
class StrawberryChannelsContext:
    """
    A Channels context for GraphQL
    """
    connection_params: Any
    request: "ChannelsConsumer"

    @property
    def ws(self):
        return self.request
