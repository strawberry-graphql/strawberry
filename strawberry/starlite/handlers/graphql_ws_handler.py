from contextlib import suppress
from typing import Any, Callable, Optional

from starlite import WebSocket
from starlite.exceptions import SerializationException, WebSocketDisconnect
from strawberry.schema import BaseSchema
from strawberry.subscriptions import GRAPHQL_WS_PROTOCOL
from strawberry.subscriptions.protocols.graphql_ws.handlers import BaseGraphQLWSHandler
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
        ws: WebSocket,
    ) -> None:
        super().__init__(schema, debug, keep_alive, keep_alive_interval)
        self._get_context = get_context
        self._get_root_value = get_root_value
        self._ws = ws

    async def get_context(self) -> Any:
        return await self._get_context()

    async def get_root_value(self) -> Any:
        return await self._get_root_value()

    async def send_json(self, data: OperationMessage) -> None:
        await self._ws.send_json(data)

    async def close(self, code: int = 1000, reason: Optional[str] = None) -> None:
        await self._ws.close(code=code, reason=reason)

    async def handle_request(self) -> Any:
        await self._ws.accept(subprotocols=GRAPHQL_WS_PROTOCOL)

        try:
            while self._ws.connection_state != "disconnect":
                try:
                    message = await self._ws.receive_json()
                except (SerializationException, ValueError):  # noqa: PERF203
                    # Ignore non-text messages
                    continue
                else:
                    await self.handle_message(message)
        except WebSocketDisconnect:  # pragma: no cover
            pass
        finally:
            if self.keep_alive_task:
                self.keep_alive_task.cancel()
                with suppress(BaseException):
                    await self.keep_alive_task

            for operation_id in list(self.subscriptions.keys()):
                await self.cleanup_operation(operation_id)
