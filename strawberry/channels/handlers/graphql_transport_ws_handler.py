from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Optional

from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL
from strawberry.subscriptions.protocols.graphql_transport_ws.handlers import (
    BaseGraphQLTransportWSHandler,
)

if TYPE_CHECKING:
    from datetime import timedelta

    from strawberry.channels.handlers.base import ChannelsWSConsumer
    from strawberry.schema import BaseSchema


class GraphQLTransportWSHandler(BaseGraphQLTransportWSHandler):
    def __init__(
        self,
        schema: BaseSchema,
        debug: bool,
        connection_init_wait_timeout: timedelta,
        get_context: Callable,
        get_root_value: Callable,
        ws: ChannelsWSConsumer,
    ) -> None:
        super().__init__(schema, debug, connection_init_wait_timeout)
        self._get_context = get_context
        self._get_root_value = get_root_value
        self._ws = ws

    async def get_context(self) -> Any:
        return await self._get_context(
            request=self._ws, connection_params=self.connection_params
        )

    async def get_root_value(self) -> Any:
        return await self._get_root_value(request=self._ws)

    async def send_json(self, data: dict) -> None:
        await self._ws.send_json(data)

    async def close(self, code: int = 1000, reason: Optional[str] = None) -> None:
        # TODO: We are using `self._ws.base_send` directly instead of `self._ws.close`
        # because the later doesn't accept the `reason` argument.
        await self._ws.base_send(
            {
                "type": "websocket.close",
                "code": code,
                "reason": reason or "",
            }
        )

    async def handle_request(self) -> Any:
        await self._ws.accept(subprotocol=GRAPHQL_TRANSPORT_WS_PROTOCOL)
        self.on_request_accepted()

    async def handle_disconnect(self, code: int) -> None:
        await self.shutdown()
