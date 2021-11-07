from datetime import timedelta
from typing import Any, Optional

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from strawberry.schema import BaseSchema
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL
from strawberry.subscriptions.protocols.graphql_transport_ws.handlers import (
    BaseGraphQLTransportWSHandler,
)


class GraphQLTransportWSHandler(BaseGraphQLTransportWSHandler):
    def __init__(
        self,
        schema: BaseSchema,
        debug: bool,
        connection_init_wait_timeout: timedelta,
        get_context,
        get_root_value,
        ws: AsyncJsonWebsocketConsumer,
    ):
        super().__init__(schema, debug, connection_init_wait_timeout)
        self._get_context = get_context
        self._get_root_value = get_root_value
        self._ws = ws

    async def get_context(self) -> Any:
        return await self._get_context(request=self._ws)

    async def get_root_value(self) -> Any:
        return await self._get_root_value(request=self._ws)

    async def send_json(self, data: dict) -> None:
        await self._ws.send_json(data)

    async def close(self, code: int = 1000, reason: Optional[str] = None) -> None:
        # Close messages are not part of the ASGI ref yet
        await self._ws.close(code=code)

    async def handle_request(self) -> Any:
        await self._ws.accept(subprotocol=GRAPHQL_TRANSPORT_WS_PROTOCOL)

    async def handle_disconnect(self, code):
        for operation_id in list(self.subscriptions.keys()):
            await self.cleanup_operation(operation_id)
