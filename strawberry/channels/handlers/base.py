from typing import Any, Dict, List, Optional, Protocol

from typing_extensions import Literal

from channels.consumer import AsyncConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from strawberry.channels.context import StrawberryChannelsContext


class ChannelsLayer(Protocol):
    """Channels layer spec.

    Based on: https://channels.readthedocs.io/en/stable/channel_layer_spec.html
    """

    # Default channels API

    extensions: List[Literal["groups", "flush"]]

    async def send(self, channel: str, message: dict) -> None:
        ...

    async def receive(self, channel: str) -> dict:
        ...

    async def new_channel(self, prefix: str = ...) -> str:
        ...

    # If groups extension is supported

    group_expiry: int

    async def group_add(self, group: str, channel: str) -> None:
        ...

    async def group_discard(self, group: str, channel: str) -> None:
        ...

    async def group_send(self, group: str, message: dict) -> None:
        ...

    # If flush extension is supported

    async def flush(self) -> None:
        ...


class ChannelsConsumer(AsyncConsumer):
    """Base channels async consumer."""

    channel_name: str
    channel_layer: ChannelsLayer

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
