from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from starlette.websockets import WebSocketDisconnect, WebSocketState

from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL
from strawberry.subscriptions.protocols.graphql_transport_ws.handlers import (
    BaseGraphQLTransportWSHandler,
)

if TYPE_CHECKING:
    from datetime import timedelta

    from starlette.websockets import WebSocket

    from strawberry.schema import BaseSchema


class GraphQLTransportWSHandler(BaseGraphQLTransportWSHandler):
    def __init__(
        self,
        schema: BaseSchema,
        debug: bool,
        connection_init_wait_timeout: timedelta,
        get_context: Callable,
        get_root_value: Callable,
        ws: WebSocket,
    ) -> None:
        super().__init__(schema, debug, connection_init_wait_timeout)
        self._get_context = get_context
        self._get_root_value = get_root_value
        self._ws = ws

    async def get_context(self) -> Any:
        return await self._get_context(request=self._ws, response=None)

    async def get_root_value(self) -> Any:
        return await self._get_root_value(request=self._ws)

    async def send_json(self, data: dict) -> None:
        await self._ws.send_json(data)

    async def close(self, code: int, reason: str) -> None:
        await self._ws.close(code=code, reason=reason)

    async def handle_request(self) -> None:
        await self._ws.accept(subprotocol=GRAPHQL_TRANSPORT_WS_PROTOCOL)
        self.on_request_accepted()

        try:
            while self._ws.application_state != WebSocketState.DISCONNECTED:
                try:
                    message = await self._ws.receive_json()
                except KeyError:  # noqa: PERF203
                    error_message = "WebSocket message type must be text"
                    await self.handle_invalid_message(error_message)
                else:
                    await self.handle_message(message)
        except WebSocketDisconnect:  # pragma: no cover
            pass
        finally:
            await self.shutdown()
