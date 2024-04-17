from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from contextlib import suppress
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    AsyncIterator,
    Callable,
    Dict,
    List,
    Optional,
)

from graphql import ExecutionResult as GraphQLExecutionResult
from graphql import GraphQLError, GraphQLSyntaxError, parse

from strawberry.subscriptions.protocols.graphql_transport_ws.types import (
    CompleteMessage,
    ConnectionAckMessage,
    ConnectionInitMessage,
    ErrorMessage,
    NextMessage,
    PingMessage,
    PongMessage,
    SubscribeMessage,
    SubscribeMessagePayload,
)
from strawberry.types.graphql import OperationType
from strawberry.unset import UNSET
from strawberry.utils.debug import pretty_print_graphql_operation
from strawberry.utils.operation import get_operation_type

if TYPE_CHECKING:
    from datetime import timedelta

    from strawberry.schema import BaseSchema
    from strawberry.subscriptions.protocols.graphql_transport_ws.types import (
        GraphQLTransportMessage,
    )
    from strawberry.types import ExecutionResult


class BaseGraphQLTransportWSHandler(ABC):
    task_logger: logging.Logger = logging.getLogger("strawberry.ws.task")

    def __init__(
        self,
        schema: BaseSchema,
        debug: bool,
        connection_init_wait_timeout: timedelta,
    ) -> None:
        self.schema = schema
        self.debug = debug
        self.connection_init_wait_timeout = connection_init_wait_timeout
        self.connection_init_timeout_task: Optional[asyncio.Task] = None
        self.connection_init_received = False
        self.connection_acknowledged = False
        self.connection_timed_out = False
        self.operations: Dict[str, Operation] = {}
        self.completed_tasks: List[asyncio.Task] = []
        self.connection_params: Optional[Dict[str, Any]] = None

    @abstractmethod
    async def get_context(self) -> Any:
        """Return the operations context"""

    @abstractmethod
    async def get_root_value(self) -> Any:
        """Return the schemas root value"""

    @abstractmethod
    async def send_json(self, data: dict) -> None:
        """Send the data JSON encoded to the WebSocket client"""

    @abstractmethod
    async def close(self, code: int, reason: str) -> None:
        """Close the WebSocket with the passed code and reason"""

    @abstractmethod
    async def handle_request(self) -> Any:
        """Handle the request this instance was created for"""

    async def handle(self) -> Any:
        return await self.handle_request()

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
            await self.close(code=4408, reason=reason)
        except Exception as error:
            await self.handle_task_exception(error)  # pragma: no cover
        finally:
            # do not clear self.connection_init_timeout_task
            # so that unittests can inspect it.
            self.completed_tasks.append(task)

    async def handle_task_exception(self, error: Exception) -> None:  # pragma: no cover
        self.task_logger.exception("Exception in worker task", exc_info=error)

    async def handle_message(self, message: dict) -> None:
        handler: Callable
        handler_arg: Any
        try:
            message_type = message.pop("type")

            if message_type == ConnectionInitMessage.type:
                handler = self.handle_connection_init
                handler_arg = ConnectionInitMessage(**message)

            elif message_type == PingMessage.type:
                handler = self.handle_ping
                handler_arg = PingMessage(**message)

            elif message_type == PongMessage.type:
                handler = self.handle_pong
                handler_arg = PongMessage(**message)

            elif message_type == SubscribeMessage.type:
                handler = self.handle_subscribe

                payload_args = message.pop("payload")

                payload = SubscribeMessagePayload(
                    query=payload_args["query"],
                    operationName=payload_args.get("operationName"),
                    variables=payload_args.get("variables"),
                    extensions=payload_args.get("extensions"),
                )
                handler_arg = SubscribeMessage(payload=payload, **message)

            elif message_type == CompleteMessage.type:
                handler = self.handle_complete
                handler_arg = CompleteMessage(**message)

            else:
                handler = self.handle_invalid_message
                handler_arg = f"Unknown message type: {message_type}"

        except (KeyError, TypeError):
            handler = self.handle_invalid_message
            handler_arg = "Failed to parse message"

        await handler(handler_arg)
        await self.reap_completed_tasks()

    async def handle_connection_init(self, message: ConnectionInitMessage) -> None:
        if self.connection_timed_out:
            # No way to reliably excercise this case during testing
            return  # pragma: no cover
        if self.connection_init_timeout_task:
            self.connection_init_timeout_task.cancel()

        payload = (
            message.payload
            if message.payload is not None and message.payload is not UNSET
            else {}
        )

        if not isinstance(payload, dict):
            await self.close(code=4400, reason="Invalid connection init payload")
            return

        self.connection_params = payload

        if self.connection_init_received:
            reason = "Too many initialisation requests"
            await self.close(code=4429, reason=reason)
            return

        self.connection_init_received = True
        await self.send_message(ConnectionAckMessage())
        self.connection_acknowledged = True

    async def handle_ping(self, message: PingMessage) -> None:
        await self.send_message(PongMessage())

    async def handle_pong(self, message: PongMessage) -> None:
        pass

    async def handle_subscribe(self, message: SubscribeMessage) -> None:
        if not self.connection_acknowledged:
            await self.close(code=4401, reason="Unauthorized")
            return

        try:
            graphql_document = parse(message.payload.query)
        except GraphQLSyntaxError as exc:
            await self.close(code=4400, reason=exc.message)
            return

        try:
            operation_type = get_operation_type(
                graphql_document, message.payload.operationName
            )
        except RuntimeError:
            await self.close(code=4400, reason="Can't get GraphQL operation type")
            return

        if message.id in self.operations:
            reason = f"Subscriber for {message.id} already exists"
            await self.close(code=4409, reason=reason)
            return

        if self.debug:  # pragma: no cover
            pretty_print_graphql_operation(
                message.payload.operationName,
                message.payload.query,
                message.payload.variables,
            )

        context = await self.get_context()
        if isinstance(context, dict):
            context["connection_params"] = self.connection_params
        root_value = await self.get_root_value()

        # Get an AsyncGenerator yielding the results
        if operation_type == OperationType.SUBSCRIPTION:
            result_source = await self.schema.subscribe(
                query=message.payload.query,
                variable_values=message.payload.variables,
                operation_name=message.payload.operationName,
                context_value=context,
                root_value=root_value,
            )
        else:
            # create AsyncGenerator returning a single result
            async def get_result_source() -> AsyncIterator[ExecutionResult]:
                yield await self.schema.execute(
                    query=message.payload.query,
                    variable_values=message.payload.variables,
                    context_value=context,
                    root_value=root_value,
                    operation_name=message.payload.operationName,
                )

            result_source = get_result_source()

        operation = Operation(self, message.id, operation_type)

        # Handle initial validation errors
        if isinstance(result_source, GraphQLExecutionResult):
            assert operation_type == OperationType.SUBSCRIPTION
            assert result_source.errors
            payload = [err.formatted for err in result_source.errors]
            await self.send_message(ErrorMessage(id=message.id, payload=payload))
            self.schema.process_errors(result_source.errors)
            return

        # Create task to handle this subscription, reserve the operation ID
        operation.task = asyncio.create_task(
            self.operation_task(result_source, operation)
        )
        self.operations[message.id] = operation

    async def operation_task(
        self, result_source: AsyncGenerator, operation: Operation
    ) -> None:
        """
        Operation task top level method.  Cleans up and de-registers the operation
        once it is done.
        """
        # TODO: Handle errors in this method using self.handle_task_exception()
        try:
            await self.handle_async_results(result_source, operation)
        except BaseException:  # pragma: no cover
            # cleanup in case of something really unexpected
            # wait for generator to be closed to ensure that any existing
            # 'finally' statement is called
            with suppress(RuntimeError):
                await result_source.aclose()
            if operation.id in self.operations:
                del self.operations[operation.id]
            raise
        else:
            await operation.send_message(CompleteMessage(id=operation.id))
        finally:
            # add this task to a list to be reaped later
            task = asyncio.current_task()
            assert task is not None
            self.completed_tasks.append(task)

    async def handle_async_results(
        self,
        result_source: AsyncGenerator,
        operation: Operation,
    ) -> None:
        try:
            async for result in result_source:
                if (
                    result.errors
                    and operation.operation_type != OperationType.SUBSCRIPTION
                ):
                    error_payload = [err.formatted for err in result.errors]
                    error_message = ErrorMessage(id=operation.id, payload=error_payload)
                    await operation.send_message(error_message)
                    # don't need to call schema.process_errors() here because
                    # it was already done by schema.execute()
                    return
                else:
                    next_payload = {"data": result.data}
                    if result.errors:
                        self.schema.process_errors(result.errors)
                        next_payload["errors"] = [
                            err.formatted for err in result.errors
                        ]
                    next_message = NextMessage(id=operation.id, payload=next_payload)
                    await operation.send_message(next_message)
        except Exception as error:
            # GraphQLErrors are handled by graphql-core and included in the
            # ExecutionResult
            error = GraphQLError(str(error), original_error=error)
            error_payload = [error.formatted]
            error_message = ErrorMessage(id=operation.id, payload=error_payload)
            await operation.send_message(error_message)
            self.schema.process_errors([error])
            return

    def forget_id(self, id: str) -> None:
        # de-register the operation id making it immediately available
        # for re-use
        del self.operations[id]

    async def handle_complete(self, message: CompleteMessage) -> None:
        await self.cleanup_operation(operation_id=message.id)

    async def handle_invalid_message(self, error_message: str) -> None:
        await self.close(code=4400, reason=error_message)

    async def send_message(self, message: GraphQLTransportMessage) -> None:
        data = message.as_dict()
        await self.send_json(data)

    async def cleanup_operation(self, operation_id: str) -> None:
        if operation_id not in self.operations:
            return
        operation = self.operations.pop(operation_id)
        assert operation.task
        operation.task.cancel()
        # do not await the task here, lest we block the main
        # websocket handler Task.

    async def reap_completed_tasks(self) -> None:
        """
        Await tasks that have completed
        """
        tasks, self.completed_tasks = self.completed_tasks, []
        for task in tasks:
            with suppress(BaseException):
                await task


class Operation:
    """
    A class encapsulating a single operation with its id.
    Helps enforce protocol state transition.
    """

    __slots__ = ["handler", "id", "operation_type", "completed", "task"]

    def __init__(
        self,
        handler: BaseGraphQLTransportWSHandler,
        id: str,
        operation_type: OperationType,
    ) -> None:
        self.handler = handler
        self.id = id
        self.operation_type = operation_type
        self.completed = False
        self.task: Optional[asyncio.Task] = None

    async def send_message(self, message: GraphQLTransportMessage) -> None:
        if self.completed:
            return
        if isinstance(message, (CompleteMessage, ErrorMessage)):
            self.completed = True
            # de-register the operation _before_ sending the final message
            self.handler.forget_id(self.id)
        await self.handler.send_message(message)
