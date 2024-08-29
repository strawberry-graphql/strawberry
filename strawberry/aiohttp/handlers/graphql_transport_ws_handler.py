from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict

from aiohttp import http, web
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL
from strawberry.subscriptions.protocols.graphql_transport_ws.handlers import (
    BaseGraphQLTransportWSHandler,
)

if TYPE_CHECKING:
    from datetime import timedelta

    from strawberry.schema import BaseSchema


class GraphQLTransportWSHandler(BaseGraphQLTransportWSHandler):
    def __init__(
        self,
        schema: BaseSchema,
        debug: bool,
        connection_init_wait_timeout: timedelta,
        get_context: Callable[..., Dict[str, Any]],
        get_root_value: Any,
        request: web.Request,
    ) -> None:
        super().__init__(schema, debug, connection_init_wait_timeout)
        self._get_context = get_context
        self._get_root_value = get_root_value
        self._request = request
        self._ws = web.WebSocketResponse(protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL])

    async def get_context(self) -> Any:
        return await self._get_context(request=self._request, response=self._ws)  # type: ignore

    async def get_root_value(self) -> Any:
        return await self._get_root_value(request=self._request)

    async def send_json(self, data: dict) -> None:
        await self._ws.send_json(data)

    async def close(self, code: int, reason: str) -> None:
        await self._ws.close(code=code, message=reason.encode())

    async def handle_request(self) -> web.StreamResponse:
        await self._ws.prepare(self._request)
        self.on_request_accepted()

        try:
            async for ws_message in self._ws:  # type: http.WSMessage
                if ws_message.type == http.WSMsgType.TEXT:
                    await self.handle_message(ws_message.json())
                else:
                    error_message = "WebSocket message type must be text"
                    await self.handle_invalid_message(error_message)
        finally:
            await self.shutdown()

        return self._ws


__all__ = ["GraphQLTransportWSHandler"]
