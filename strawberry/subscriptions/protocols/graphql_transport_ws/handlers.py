from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable
from contextlib import suppress
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Optional,
    cast,
)

from graphql import GraphQLError, GraphQLSyntaxError, parse

from strawberry.exceptions import ConnectionRejectionError
from strawberry.http.exceptions import (
    NonJsonMessageReceived,
    NonTextMessageReceived,
    WebSocketDisconnected,
)
from strawberry.http.typevars import Context, RootValue
from strawberry.subscriptions.protocols.graphql_transport_ws.types import (
    CompleteMessage,
    ConnectionInitMessage,
    Message,
    NextMessagePayload,
    PingMessage,
    PongMessage,
    SubscribeMessage,
)
from strawberry.types import ExecutionResult
from strawberry.types.execution import PreExecutionError
from strawberry.types.graphql import OperationType
from strawberry.types.unset import UnsetType
from strawberry.utils.debug import pretty_print_graphql_operation
from strawberry.utils.operation import get_operation_type

if TYPE_CHECKING:
    from collections.abc import Awaitable
    from datetime import timedelta

    from strawberry.http.async_base_view import AsyncBaseHTTPView, AsyncWebSocketAdapter
    from strawberry.schema import BaseSchema
    from strawberry.schema.subscribe import SubscriptionResult


class BaseGraphQLTransportWSHandler(Generic[Context, RootValue]):
    task_logger: logging.Logger = logging.getLogger("strawberry.ws.task")

    def __init__(
        self,
        view: AsyncBaseHTTPView[Any, Any, Any, Any, Any, Context, RootValue],
        websocket: AsyncWebSocketAdapter,
        context: Context,
        root_value: RootValue,
        schema: BaseSchema,
        debug: bool,
        connection_init_wait_timeout: timedelta,
    ) -> None:
        self.view = view
        self.websocket = websocket
        self.context = context
        self.root_value = root_value
        self.schema = schema
        self.debug = debug
        self.connection_init_wait_timeout = connection_init_wait_timeout
        self.connection_init_timeout_task: Optional[asyncio.Task] = None
        self.connection_init_received = False
        self.connection_acknowledged = False
        self.connection_timed_out = False
        self.operations: dict[str, Operation[Context, RootValue]] = {}
        self.completed_tasks: list[asyncio.Task] = []

    async def handle(self) -> None:
        self.on_request_accepted()

        try:
            try:
                async for message in self.websocket.iter_json():
                    await self.handle_message(cast(Message, message))
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

        for operation_id in list(self.operations.keys()):
            await self.cleanup_operation(operation_id)
        await self.reap_completed_tasks()

    def on_request_accepted(self) -> None:
        # handle_request should call this once it has sent the
        # websocket.accept() response to start the timeout.
        assert not self.connection_init_timeout_task
        self.connection_init_timeout_task = asyncio.create_task(
            self.handle_connection_init_timeout()
        )

    async def handle_connection_init_timeout(self) -> None:
        task = asyncio.current_task()
        assert task
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
        finally:
            # do not clear self.connection_init_timeout_task
            # so that unittests can inspect it.
            self.completed_tasks.append(task)

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
        finally:
            await self.reap_completed_tasks()

    async def handle_connection_init(self, message: ConnectionInitMessage) -> None:
        if self.connection_timed_out:
            # No way to reliably excercise this case during testing
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

        self.context = cast(Context, self.context)

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

        try:
            graphql_document = parse(message["payload"]["query"])
        except GraphQLSyntaxError as exc:
            await self.websocket.close(code=4400, reason=exc.message)
            return

        try:
            operation_type = get_operation_type(
                graphql_document, message["payload"].get("operationName")
            )
        except RuntimeError:
            await self.websocket.close(
                code=4400, reason="Can't get GraphQL operation type"
            )
            return

        if message["id"] in self.operations:
            reason = f"Subscriber for {message['id']} already exists"
            await self.websocket.close(code=4409, reason=reason)
            return

        if self.debug:  # pragma: no cover
            pretty_print_graphql_operation(
                message["payload"].get("operationName"),
                message["payload"]["query"],
                message["payload"].get("variables"),
            )

        operation = Operation(
            self,
            message["id"],
            operation_type,
            message["payload"]["query"],
            message["payload"].get("variables"),
            message["payload"].get("operationName"),
        )

        operation.task = asyncio.create_task(self.run_operation(operation))
        self.operations[message["id"]] = operation

    async def run_operation(self, operation: Operation[Context, RootValue]) -> None:
        """The operation task's top level method. Cleans-up and de-registers the operation once it is done."""
        # TODO: Handle errors in this method using self.handle_task_exception()

        result_source: Awaitable[ExecutionResult] | Awaitable[SubscriptionResult]

        # Get an AsyncGenerator yielding the results
        if operation.operation_type == OperationType.SUBSCRIPTION:
            result_source = self.schema.subscribe(
                query=operation.query,
                variable_values=operation.variables,
                operation_name=operation.operation_name,
                context_value=self.context,
                root_value=self.root_value,
            )
        else:
            result_source = self.schema.execute(
                query=operation.query,
                variable_values=operation.variables,
                context_value=self.context,
                root_value=self.root_value,
                operation_name=operation.operation_name,
            )

        try:
            first_res_or_agen = await result_source
            # that's an immediate error we should end the operation
            # without a COMPLETE message
            if isinstance(first_res_or_agen, PreExecutionError):
                assert first_res_or_agen.errors
                await operation.send_initial_errors(first_res_or_agen.errors)
            # that's a mutation / query result
            elif isinstance(first_res_or_agen, ExecutionResult):
                await operation.send_next(first_res_or_agen)
                await operation.send_operation_message(
                    {"id": operation.id, "type": "complete"}
                )
            else:
                async for result in first_res_or_agen:
                    await operation.send_next(result)
                await operation.send_operation_message(
                    {"id": operation.id, "type": "complete"}
                )

        except BaseException:  # pragma: no cover
            self.operations.pop(operation.id, None)
            raise
        finally:
            # add this task to a list to be reaped later
            task = asyncio.current_task()
            assert task is not None
            self.completed_tasks.append(task)

    def forget_id(self, id: str) -> None:
        # de-register the operation id making it immediately available
        # for re-use
        del self.operations[id]

    async def handle_complete(self, message: CompleteMessage) -> None:
        await self.cleanup_operation(operation_id=message["id"])

    async def handle_invalid_message(self, error_message: str) -> None:
        await self.websocket.close(code=4400, reason=error_message)

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

    async def reap_completed_tasks(self) -> None:
        """Await tasks that have completed."""
        tasks, self.completed_tasks = self.completed_tasks, []
        for task in tasks:
            with suppress(BaseException):
                await task


class Operation(Generic[Context, RootValue]):
    """A class encapsulating a single operation with its id. Helps enforce protocol state transition."""

    __slots__ = [
        "completed",
        "handler",
        "id",
        "operation_name",
        "operation_type",
        "query",
        "task",
        "variables",
    ]

    def __init__(
        self,
        handler: BaseGraphQLTransportWSHandler[Context, RootValue],
        id: str,
        operation_type: OperationType,
        query: str,
        variables: Optional[dict[str, object]],
        operation_name: Optional[str],
    ) -> None:
        self.handler = handler
        self.id = id
        self.operation_type = operation_type
        self.query = query
        self.variables = variables
        self.operation_name = operation_name
        self.completed = False
        self.task: Optional[asyncio.Task] = None

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
