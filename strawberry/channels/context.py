from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from strawberry.channels.handlers.base import ChannelsConsumer


@dataclass
class StrawberryChannelsContext:
    """
    A Channels context for GraphQL
    """

    request: "ChannelsConsumer"
    connection_params: Optional[Dict[str, Any]] = None

    @property
    def ws(self):
        return self.request

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)
