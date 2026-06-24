from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    cast,
)

from graphql import GraphQLError, GraphQLSyntaxError

from strawberry.exceptions import ConnectionRejectionError
from strawberry.http.exceptions import (
    NonJsonMessageReceived,
    NonTextMessageReceived,
    WebSocketDisconnected,
)
from strawberry.http.typevars import Context, RootValue
from strawberry.schema.exceptions import CannotGetOperationTypeError
from strawberry.subscriptions.protocols.graphql_transport_ws.types import (
    CompleteMessage,
    ConnectionInitMessage,
    Message,
    NextMessagePayload,
    PingMessage,
    PongMessage,
    SubscribeMessage,
)
from strawberry.types.execution import ExecutionResult, PreExecutionError
from strawberry.types.unset import UnsetType
from strawberry.utils.aio import aclosing

if TYPE_CHECKING:
    from datetime import timedelta

    from strawberry.http.async_base_view import AsyncBaseHTTPView, AsyncWebSocketAdapter
    from strawberry.schema import BaseSchema
    from strawberry.schema.schema import StreamResult


class _OperationStreamClosed(Exception):
    """Raised when an operation closes the websocket instead of completing."""


class BaseGraphQLTransportWSHandler(Generic[Context, RootValue]):
    task_logger: logging.Logger = logging.getLogger("strawberry.ws.task")

    def __init__(
        self,
        view: AsyncBaseHTTPView[Any, Any, Any, Any, Any, Context, RootValue],
        websocket: AsyncWebSocketAdapter,
        context: Context,
        root_value: RootValue | None,
        schema: BaseSchema,
        connection_init_wait_timeout: timedelta,
        max_subscriptions_per_connection: int | None = None,
    ) -> None:
        self.view = view
        self.websocket = websocket
        self.context = context
        self.root_value = root_value
        self.schema = schema
        self.connection_init_wait_timeout = connection_init_wait_timeout
        self.max_subscriptions_per_connection = max_subscriptions_per_connection
        self.connection_init_timeout_task: asyncio.Task | None = None
        self.connection_init_received = False
        self.connection_acknowledged = False
        self.connection_timed_out = False
        self.operations: dict[str, Operation[Context, RootValue]] = {}

    async def handle(self) -> None:
        self.on_request_accepted()

        try:
            try:
                async for message in self.websocket.iter_json():
                    await self.handle_message(cast("Message", message))
            except NonTextMessageReceived:
                await self.handle_invalid_message("WebSocket message type must be text")
            except NonJsonMessageReceived:
                await self.handle_invalid_message(
                    "WebSocket message must be valid JSON"
                )
        except WebSocketDisconnected:
            pass
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        if self.connection_init_timeout_task:
            self.connection_init_timeout_task.cancel()
            with suppress(asyncio.CancelledError):
                await self.connection_init_timeout_task

        tasks = [op.task for op in self.operations.values() if op.task]
        for operation_id in list(self.operations.keys()):
            await self.cleanup_operation(operation_id)
        # Let cancelled tasks finish their finally blocks before shutdown returns.
        # Per-task suppress survives parent cancellation; asyncio.gather would not.
        for task in tasks:
            with suppress(Exception, asyncio.CancelledError):
                await task

    def on_request_accepted(self) -> None:
        # handle_request should call this once it has sent the
        # websocket.accept() response to start the timeout.
        assert not self.connection_init_timeout_task
        self.connection_init_timeout_task = asyncio.create_task(
            self.handle_connection_init_timeout()
        )
        self.connection_init_timeout_task.add_done_callback(self._task_done)

    async def handle_connection_init_timeout(self) -> None:
        try:
            delay = self.connection_init_wait_timeout.total_seconds()
            await asyncio.sleep(delay=delay)

            if self.connection_init_received:
                return  # pragma: no cover

            self.connection_timed_out = True
            reason = "Connection initialisation timeout"
            await self.websocket.close(code=4408, reason=reason)
        except Exception as error:  # noqa: BLE001
            await self.handle_task_exception(error)  # pragma: no cover

    def _task_done(self, task: asyncio.Task) -> None:
        if task.cancelled():
            return
        # Retrieve exception to prevent "Task exception was never retrieved" warning.
        # Exceptions are already logged by handle_task_exception in the coroutines.
        task.exception()

    async def handle_task_exception(self, error: Exception) -> None:  # pragma: no cover
        self.task_logger.exception("Exception in worker task", exc_info=error)

    async def handle_message(self, message: Message) -> None:
        try:
            if message["type"] == "connection_init":
                await self.handle_connection_init(message)

            elif message["type"] == "ping":
                await self.handle_ping(message)

            elif message["type"] == "pong":
                await self.handle_pong(message)

            elif message["type"] == "subscribe":
                await self.handle_subscribe(message)

            elif message["type"] == "complete":
                await self.handle_complete(message)

            else:
                error_message = f"Unknown message type: {message['type']}"
                await self.handle_invalid_message(error_message)

        except KeyError:
            await self.handle_invalid_message("Failed to parse message")

    async def handle_connection_init(self, message: ConnectionInitMessage) -> None:
        if self.connection_timed_out:
            # No way to reliably exercise this case during testing
            return  # pragma: no cover

        if self.connection_init_timeout_task:
            self.connection_init_timeout_task.cancel()

        payload = message.get("payload", {})

        if not isinstance(payload, dict):
            await self.websocket.close(
                code=4400, reason="Invalid connection init payload"
            )
            return

        if self.connection_init_received:
            reason = "Too many initialisation requests"
            await self.websocket.close(code=4429, reason=reason)
            return

        self.connection_init_received = True

        if isinstance(self.context, dict):
            self.context["connection_params"] = payload
        elif hasattr(self.context, "connection_params"):
            self.context.connection_params = payload

        try:
            connection_ack_payload = await self.view.on_ws_connect(self.context)
        except ConnectionRejectionError:
            await self.websocket.close(code=4403, reason="Forbidden")
            return

        if isinstance(connection_ack_payload, UnsetType):
            await self.send_message({"type": "connection_ack"})
        else:
            await self.send_message(
                {"type": "connection_ack", "payload": connection_ack_payload}
            )

        self.connection_acknowledged = True

    async def handle_ping(self, message: PingMessage) -> None:
        await self.send_message({"type": "pong"})

    async def handle_pong(self, message: PongMessage) -> None:
        pass

    async def handle_subscribe(self, message: SubscribeMessage) -> None:
        if not self.connection_acknowledged:
            await self.websocket.close(code=4401, reason="Unauthorized")
            return

        if message["id"] in self.operations:
            reason = f"Subscriber for {message['id']} already exists"
            await self.websocket.close(code=4409, reason=reason)
            return

        # NOTE: this applies to all in-flight operations (queries and mutations
        # executed over WebSocket included), not only subscriptions.
        if (
            self.max_subscriptions_per_connection is not None
            and len(self.operations) >= self.max_subscriptions_per_connection
        ):
            error = GraphQLError("Subscription limit reached")
            await self.send_message(
                {
                    "id": message["id"],
                    "type": "error",
                    "payload": [error.formatted],
                }
            )
            return

        operation = Operation(
            self,
            message["id"],
            message["payload"]["query"],
            message["payload"].get("variables"),
            message["payload"].get("operationName"),
        )

        operation.task = asyncio.create_task(self.run_operation(operation))
        operation.task.add_done_callback(self._task_done)
        self.operations[message["id"]] = operation

    async def run_operation(self, operation: Operation[Context, RootValue]) -> None:
        """The operation task's top level method. Cleans-up and de-registers the operation once it is done."""
        try:
            result_source = await self.schema.stream(
                operation.query,
                variable_values=operation.variables,
                context_value=self.context,
                root_value=self.root_value,
                operation_name=operation.operation_name,
            )

            async with aclosing(result_source):
                await self._send_result_stream(operation, result_source)

            await operation.send_operation_message(
                CompleteMessage(id=operation.id, type="complete")
            )

        except _OperationStreamClosed:
            return
        except Exception as error:  # pragma: no cover
            await self.handle_task_exception(error)

            with suppress(Exception):
                await operation.send_operation_message(
                    {"id": operation.id, "type": "complete"}
                )

            self.operations.pop(operation.id, None)

            raise

    async def _send_result_stream(
        self,
        operation: Operation[Context, RootValue],
        result_source: StreamResult,
    ) -> None:
        is_first_result = True

        async for result in result_source:
            if is_first_result and isinstance(result, PreExecutionError):
                await self._handle_pre_execution_error(operation, result)
                return

            if not isinstance(result, ExecutionResult):
                await self._reject_incremental_delivery(operation)
                return

            await operation.send_next(result)
            is_first_result = False

    async def _handle_pre_execution_error(
        self,
        operation: Operation[Context, RootValue],
        result: PreExecutionError,
    ) -> None:
        assert result.errors
        if close_reason := self._get_pre_execution_close_reason(result.errors[0]):
            await self.websocket.close(code=4400, reason=close_reason)
            self.operations.pop(operation.id, None)
            raise _OperationStreamClosed

        await operation.send_initial_errors(result.errors)

    async def _reject_incremental_delivery(
        self, operation: Operation[Context, RootValue]
    ) -> None:
        # Incremental delivery (``@defer``/``@stream``) yields raw graphql-core
        # frames that the graphql-transport-ws ``next`` message has no wire
        # representation for. Reject the operation rather than send a malformed
        # or partial payload.
        await operation.send_initial_errors(
            [
                GraphQLError(
                    "Incremental delivery is not supported over graphql-transport-ws"
                )
            ]
        )

    def forget_id(self, id: str) -> None:
        # de-register the operation id making it immediately available
        # for reuse
        del self.operations[id]

    async def handle_complete(self, message: CompleteMessage) -> None:
        await self.cleanup_operation(operation_id=message["id"])

    async def handle_invalid_message(self, error_message: str) -> None:
        await self.websocket.close(code=4400, reason=error_message)

    @staticmethod
    def _get_pre_execution_close_reason(error: GraphQLError) -> str | None:
        if isinstance(error, GraphQLSyntaxError):
            return error.message

        if isinstance(error.original_error, CannotGetOperationTypeError):
            return error.original_error.as_http_error_reason()

        return None

    async def send_message(self, message: Message) -> None:
        await self.websocket.send_json(message)

    async def cleanup_operation(self, operation_id: str) -> None:
        if operation_id not in self.operations:
            return
        operation = self.operations.pop(operation_id)
        assert operation.task
        operation.task.cancel()
        # do not await the task here, lest we block the main
        # websocket handler Task.


class Operation(Generic[Context, RootValue]):
    """A class encapsulating a single operation with its id. Helps enforce protocol state transition."""

    __slots__ = [
        "completed",
        "handler",
        "id",
        "operation_name",
        "query",
        "task",
        "variables",
    ]

    def __init__(
        self,
        handler: BaseGraphQLTransportWSHandler[Context, RootValue],
        id: str,
        query: str,
        variables: dict[str, object] | None,
        operation_name: str | None,
    ) -> None:
        self.handler = handler
        self.id = id
        self.query = query
        self.variables = variables
        self.operation_name = operation_name
        self.completed = False
        self.task: asyncio.Task | None = None

    async def send_operation_message(self, message: Message) -> None:
        if self.completed:
            return
        if message["type"] == "complete" or message["type"] == "error":
            self.completed = True
            # de-register the operation _before_ sending the final message
            self.handler.forget_id(self.id)
        await self.handler.send_message(message)

    async def send_initial_errors(self, errors: list[GraphQLError]) -> None:
        # Initial errors see https://github.com/enisdenjo/graphql-ws/blob/master/PROTOCOL.md#error
        # "This can occur before execution starts,
        # usually due to validation errors, or during the execution of the request"
        await self.send_operation_message(
            {
                "id": self.id,
                "type": "error",
                "payload": [err.formatted for err in errors],
            }
        )

    async def send_next(self, execution_result: ExecutionResult) -> None:
        next_payload: NextMessagePayload = {"data": execution_result.data}

        if execution_result.errors:
            next_payload["errors"] = [err.formatted for err in execution_result.errors]

        if execution_result.extensions:
            next_payload["extensions"] = execution_result.extensions

        await self.send_operation_message(
            {"id": self.id, "type": "next", "payload": next_payload}
        )


__all__ = ["BaseGraphQLTransportWSHandler", "Operation"]
