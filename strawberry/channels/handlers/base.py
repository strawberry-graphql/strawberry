from typing import Any, Dict, Optional

from channels.consumer import AsyncConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from strawberry.channels.context import StrawberryChannelsContext


class ChannelsConsumer(AsyncConsumer):
    """Base channels async consumer."""

    @property
    def headers(self) -> Dict[str, str]:
        return {
            header_name.decode().lower(): header_value.decode()
            for header_name, header_value in self.scope["headers"]
        }

    async def get_root_value(self, request: Optional["ChannelsConsumer"] = None) -> Any:
        return None

    async def get_context(
        self,
        request: Optional["ChannelsConsumer"] = None,
    ) -> StrawberryChannelsContext:
        return StrawberryChannelsContext(request=request or self)


class ChannelsWSConsumer(ChannelsConsumer, AsyncJsonWebsocketConsumer):
    """Base channels websocket async consumer."""
