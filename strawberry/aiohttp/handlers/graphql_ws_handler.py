from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any, Callable, Optional

from aiohttp import http, web
from strawberry.subscriptions import GRAPHQL_WS_PROTOCOL
from strawberry.subscriptions.protocols.graphql_ws.handlers import BaseGraphQLWSHandler

if TYPE_CHECKING:
    from strawberry.schema import BaseSchema
    from strawberry.subscriptions.protocols.graphql_ws.types import OperationMessage


class GraphQLWSHandler(BaseGraphQLWSHandler):
    def __init__(
        self,
        schema: BaseSchema,
        debug: bool,
        keep_alive: bool,
        keep_alive_interval: float,
        get_context: Callable,
        get_root_value: Callable,
        request: web.Request,
    ) -> None:
        super().__init__(schema, debug, keep_alive, keep_alive_interval)
        self._get_context = get_context
        self._get_root_value = get_root_value
        self._request = request
        self._ws = web.WebSocketResponse(protocols=[GRAPHQL_WS_PROTOCOL])

    async def get_context(self) -> Any:
        return await self._get_context(request=self._request, response=self._ws)

    async def get_root_value(self) -> Any:
        return await self._get_root_value(request=self._request)

    async def send_json(self, data: OperationMessage) -> None:
        await self._ws.send_json(data)

    async def close(self, code: int = 1000, reason: Optional[str] = None) -> None:
        message = reason.encode() if reason else b""
        await self._ws.close(code=code, message=message)

    async def handle_request(self) -> Any:
        await self._ws.prepare(self._request)

        try:
            async for ws_message in self._ws:  # type: http.WSMessage
                if ws_message.type == http.WSMsgType.TEXT:
                    message: OperationMessage = ws_message.json()
                    await self.handle_message(message)
        finally:
            if self.keep_alive_task:
                self.keep_alive_task.cancel()
                with suppress(BaseException):
                    await self.keep_alive_task

            for operation_id in list(self.subscriptions.keys()):
                await self.cleanup_operation(operation_id)

        return self._ws


__all__ = ["GraphQLWSHandler"]
