from __future__ import annotations

import asyncio
from contextlib import suppress
from typing import (
    TYPE_CHECKING,
    AsyncGenerator,
    Dict,
    Optional,
    cast,
)

from strawberry.http.exceptions import NonTextMessageReceived, WebSocketDisconnected
from strawberry.subscriptions.protocols.graphql_ws.types import (
    CompleteMessage,
    ConnectionAckMessage,
    ConnectionErrorMessage,
    ConnectionInitMessage,
    ConnectionKeepAliveMessage,
    ConnectionTerminateMessage,
    DataMessage,
    ErrorMessage,
    OperationMessage,
    StartMessage,
    StopMessage,
)
from strawberry.types.execution import ExecutionResult, PreExecutionError
from strawberry.utils.debug import pretty_print_graphql_operation

if TYPE_CHECKING:
    from strawberry.http.async_base_view import AsyncWebSocketAdapter
    from strawberry.schema import BaseSchema


class BaseGraphQLWSHandler:
    def __init__(
        self,
        websocket: AsyncWebSocketAdapter,
        context: object,
        root_value: object,
        schema: BaseSchema,
        debug: bool,
        keep_alive: bool,
        keep_alive_interval: Optional[float],
    ) -> None:
        self.websocket = websocket
        self.context = context
        self.root_value = root_value
        self.schema = schema
        self.debug = debug
        self.keep_alive = keep_alive
        self.keep_alive_interval = keep_alive_interval
        self.keep_alive_task: Optional[asyncio.Task] = None
        self.subscriptions: Dict[str, AsyncGenerator] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        self.connection_params: Optional[Dict[str, object]] = None

    async def handle(self) -> None:
        try:
            try:
                async for message in self.websocket.iter_json(
                    ignore_parsing_errors=True
                ):
                    await self.handle_message(cast(OperationMessage, message))
            except NonTextMessageReceived:
                await self.websocket.close(
                    code=1002, reason="WebSocket message type must be text"
                )
        except WebSocketDisconnected:
            pass
        finally:
            if self.keep_alive_task:
                self.keep_alive_task.cancel()
                with suppress(BaseException):
                    await self.keep_alive_task

            for operation_id in list(self.subscriptions.keys()):
                await self.cleanup_operation(operation_id)

    async def handle_message(
        self,
        message: OperationMessage,
    ) -> None:
        if message["type"] == "connection_init":
            await self.handle_connection_init(message)
        elif message["type"] == "connection_terminate":
            await self.handle_connection_terminate(message)
        elif message["type"] == "start":
            await self.handle_start(message)
        elif message["type"] == "stop":
            await self.handle_stop(message)

    async def handle_connection_init(self, message: ConnectionInitMessage) -> None:
        payload = message.get("payload")
        if payload is not None and not isinstance(payload, dict):
            error_message: ConnectionErrorMessage = {"type": "connection_error"}
            await self.websocket.send_json(error_message)
            await self.websocket.close(code=1000, reason="")
            return

        self.connection_params = payload

        connection_ack_message: ConnectionAckMessage = {"type": "connection_ack"}
        await self.websocket.send_json(connection_ack_message)

        if self.keep_alive:
            keep_alive_handler = self.handle_keep_alive()
            self.keep_alive_task = asyncio.create_task(keep_alive_handler)

    async def handle_connection_terminate(
        self, message: ConnectionTerminateMessage
    ) -> None:
        await self.websocket.close(code=1000, reason="")

    async def handle_start(self, message: StartMessage) -> None:
        operation_id = message["id"]
        payload = message["payload"]
        query = payload["query"]
        operation_name = payload.get("operationName")
        variables = payload.get("variables")

        if isinstance(self.context, dict):
            self.context["connection_params"] = self.connection_params
        elif hasattr(self.context, "connection_params"):
            self.context.connection_params = self.connection_params

        if self.debug:
            pretty_print_graphql_operation(operation_name, query, variables)

        result_handler = self.handle_async_results(
            operation_id, query, operation_name, variables
        )
        self.tasks[operation_id] = asyncio.create_task(result_handler)

    async def handle_stop(self, message: StopMessage) -> None:
        operation_id = message["id"]
        await self.cleanup_operation(operation_id)

    async def handle_keep_alive(self) -> None:
        assert self.keep_alive_interval
        while True:
            data: ConnectionKeepAliveMessage = {"type": "ka"}
            await self.websocket.send_json(data)
            await asyncio.sleep(self.keep_alive_interval)

    async def handle_async_results(
        self,
        operation_id: str,
        query: str,
        operation_name: Optional[str],
        variables: Optional[Dict[str, object]],
    ) -> None:
        try:
            agen_or_err = await self.schema.subscribe(
                query=query,
                variable_values=variables,
                operation_name=operation_name,
                context_value=self.context,
                root_value=self.root_value,
            )
            if isinstance(agen_or_err, PreExecutionError):
                assert agen_or_err.errors
                error_payload = agen_or_err.errors[0].formatted
                error_message: ErrorMessage = {
                    "type": "error",
                    "id": operation_id,
                    "payload": error_payload,
                }
                await self.websocket.send_json(error_message)
            else:
                self.subscriptions[operation_id] = agen_or_err

                async for result in agen_or_err:
                    await self.send_data(result, operation_id)

                await self.websocket.send_json(
                    CompleteMessage({"type": "complete", "id": operation_id})
                )
        except asyncio.CancelledError:
            await self.websocket.send_json(
                CompleteMessage({"type": "complete", "id": operation_id})
            )

    async def cleanup_operation(self, operation_id: str) -> None:
        if operation_id in self.subscriptions:
            with suppress(RuntimeError):
                await self.subscriptions[operation_id].aclose()
            del self.subscriptions[operation_id]

        self.tasks[operation_id].cancel()
        with suppress(BaseException):
            await self.tasks[operation_id]
        del self.tasks[operation_id]

    async def send_data(
        self, execution_result: ExecutionResult, operation_id: str
    ) -> None:
        data_message: DataMessage = {
            "type": "data",
            "id": operation_id,
            "payload": {"data": execution_result.data},
        }

        if execution_result.errors:
            data_message["payload"]["errors"] = [
                err.formatted for err in execution_result.errors
            ]

        if execution_result.extensions:
            data_message["payload"]["extensions"] = execution_result.extensions

        await self.websocket.send_json(data_message)


__all__ = ["BaseGraphQLWSHandler"]
