from contextlib import suppress
from typing import Any, Optional

from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

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
        get_context,
        get_root_value,
        ws: WebSocket,
    ):
        super().__init__(schema, debug, keep_alive, keep_alive_interval)
        self._get_context = get_context
        self._get_root_value = get_root_value
        self._ws = ws

    async def get_context(self) -> Any:
        return await self._get_context(request=self._ws)

    async def get_root_value(self) -> Any:
        return await self._get_root_value(request=self._ws)

    async def send_json(self, data: OperationMessage) -> None:
        await self._ws.send_json(data)

    async def close(self, code: int = 1000, reason: Optional[str] = None) -> None:
        # Close messages are not part of the ASGI ref yet
        await self._ws.close(code=code)

    async def handle_request(self) -> Any:
        await self._ws.accept(subprotocol=GRAPHQL_WS_PROTOCOL)

        try:
            while self._ws.application_state != WebSocketState.DISCONNECTED:
                try:
                    message = await self._ws.receive_json()
                except KeyError:
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
