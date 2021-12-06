import asyncio
from abc import ABC, abstractmethod
from contextlib import suppress
from datetime import timedelta
from typing import Any, AsyncGenerator, Dict, Optional

from graphql import ExecutionResult as GraphQLExecutionResult, GraphQLError
from graphql.error import format_error as format_graphql_error

from strawberry.schema import BaseSchema
from strawberry.subscriptions.protocols.graphql_transport_ws.types import (
    CompleteMessage,
    ConnectionAckMessage,
    ConnectionInitMessage,
    ErrorMessage,
    GraphQLTransportMessage,
    NextMessage,
    PingMessage,
    PongMessage,
    SubscribeMessage,
    SubscribeMessagePayload,
)
from strawberry.utils.debug import pretty_print_graphql_operation


class BaseGraphQLTransportWSHandler(ABC):
    def __init__(
        self,
        schema: BaseSchema,
        debug: bool,
        connection_init_wait_timeout: timedelta,
    ):
        self.schema = schema
        self.debug = debug
        self.connection_init_wait_timeout = connection_init_wait_timeout
        self.connection_init_timeout_task: Optional[asyncio.Task] = None
        self.connection_init_received = False
        self.connection_acknowledged = False
        self.subscriptions: Dict[str, AsyncGenerator] = {}
        self.tasks: Dict[str, asyncio.Task] = {}

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
        timeout_handler = self.handle_connection_init_timeout()
        self.connection_init_timeout_task = asyncio.create_task(timeout_handler)
        return await self.handle_request()

    async def handle_connection_init_timeout(self):
        delay = self.connection_init_wait_timeout.total_seconds()
        await asyncio.sleep(delay=delay)

        if self.connection_init_received:
            return

        reason = "Connection initialisation timeout"
        await self.close(code=4408, reason=reason)

    async def handle_message(self, message: dict):
        try:
            message_type = message.pop("type")

            if message_type == ConnectionInitMessage.type:
                await self.handle_connection_init(ConnectionInitMessage(**message))

            elif message_type == PingMessage.type:
                await self.handle_ping(PingMessage(**message))

            elif message_type == PongMessage.type:
                await self.handle_pong(PongMessage(**message))

            elif message_type == SubscribeMessage.type:
                payload = SubscribeMessagePayload(**message.pop("payload"))
                await self.handle_subscribe(
                    SubscribeMessage(payload=payload, **message)
                )

            elif message_type == CompleteMessage.type:
                await self.handle_complete(CompleteMessage(**message))

            else:
                error_message = f"Unknown message type: {message_type}"
                await self.handle_invalid_message(error_message)

        except (KeyError, TypeError):
            error_message = "Failed to parse message"
            await self.handle_invalid_message(error_message)

    async def handle_connection_init(self, message: ConnectionInitMessage) -> None:
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

        if message.id in self.subscriptions.keys():
            reason = f"Subscriber for {message.id} already exists"
            await self.close(code=4409, reason=reason)
            return

        context = await self.get_context()
        root_value = await self.get_root_value()

        if self.debug:  # pragma: no cover
            pretty_print_graphql_operation(
                message.payload.operationName,
                message.payload.query,
                message.payload.variables,
            )

        try:
            result_source = await self.schema.subscribe(
                query=message.payload.query,
                variable_values=message.payload.variables,
                operation_name=message.payload.operationName,
                context_value=context,
                root_value=root_value,
            )
        except GraphQLError as error:
            payload = [format_graphql_error(error)]
            await self.send_message(ErrorMessage(id=message.id, payload=payload))
            self.schema.process_errors([error])
            return

        if isinstance(result_source, GraphQLExecutionResult):
            assert result_source.errors
            payload = [format_graphql_error(result_source.errors[0])]
            await self.send_message(ErrorMessage(id=message.id, payload=payload))
            self.schema.process_errors(result_source.errors)
            return

        handler = self.handle_async_results(result_source, message.id)
        self.subscriptions[message.id] = result_source
        self.tasks[message.id] = asyncio.create_task(handler)

    async def handle_async_results(
        self,
        result_source: AsyncGenerator,
        operation_id: str,
    ) -> None:
        try:
            async for result in result_source:
                if result.errors:
                    error_payload = [format_graphql_error(err) for err in result.errors]
                    error_message = ErrorMessage(id=operation_id, payload=error_payload)
                    await self.send_message(error_message)
                    self.schema.process_errors(result.errors)
                    return
                else:
                    next_payload = {"data": result.data}
                    next_message = NextMessage(id=operation_id, payload=next_payload)
                    await self.send_message(next_message)
        except asyncio.CancelledError:
            # CancelledErrors are expected during task cleanup.
            return
        except Exception as error:
            # GraphQLErrors are handled by graphql-core and included in the
            # ExecutionResult
            error = GraphQLError(str(error), original_error=error)
            error_payload = [format_graphql_error(error)]
            error_message = ErrorMessage(id=operation_id, payload=error_payload)
            await self.send_message(error_message)
            self.schema.process_errors([error])
            return

        await self.send_message(CompleteMessage(id=operation_id))

    async def handle_complete(self, message: CompleteMessage) -> None:
        await self.cleanup_operation(operation_id=message.id)

    async def handle_invalid_message(self, error_message: str) -> None:
        await self.close(code=4400, reason=error_message)

    async def send_message(self, message: GraphQLTransportMessage) -> None:
        data = message.as_dict()
        await self.send_json(data)

    async def cleanup_operation(self, operation_id: str) -> None:
        await self.subscriptions[operation_id].aclose()
        del self.subscriptions[operation_id]

        self.tasks[operation_id].cancel()
        with suppress(BaseException):
            await self.tasks[operation_id]
        del self.tasks[operation_id]
