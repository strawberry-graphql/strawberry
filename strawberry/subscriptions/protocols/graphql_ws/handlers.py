import asyncio
from abc import ABC, abstractmethod
from contextlib import suppress
from typing import Any, AsyncGenerator, Dict, Optional, cast

from graphql import ExecutionResult as GraphQLExecutionResult, GraphQLError
from graphql.error import format_error as format_graphql_error

from strawberry.schema import BaseSchema
from strawberry.subscriptions.protocols.graphql_ws import (
    GQL_COMPLETE,
    GQL_CONNECTION_ACK,
    GQL_CONNECTION_INIT,
    GQL_CONNECTION_KEEP_ALIVE,
    GQL_CONNECTION_TERMINATE,
    GQL_DATA,
    GQL_ERROR,
    GQL_START,
    GQL_STOP,
)
from strawberry.subscriptions.protocols.graphql_ws.types import (
    OperationMessage,
    OperationMessagePayload,
    StartPayload,
)
from strawberry.utils.debug import pretty_print_graphql_operation


class BaseGraphQLWSHandler(ABC):
    def __init__(
        self,
        schema: BaseSchema,
        debug: bool,
        keep_alive: bool,
        keep_alive_interval: float,
    ):
        self.schema = schema
        self.debug = debug
        self.keep_alive = keep_alive
        self.keep_alive_interval = keep_alive_interval
        self.keep_alive_task: Optional[asyncio.Task] = None
        self.subscriptions: Dict[str, AsyncGenerator] = {}
        self.tasks: Dict[str, asyncio.Task] = {}

    @abstractmethod
    async def get_context(self) -> Any:
        """Return the operations context"""

    @abstractmethod
    async def get_root_value(self) -> Any:
        """Return the schemas root value"""

    @abstractmethod
    async def send_json(self, data: OperationMessage) -> None:
        """Send the data JSON encoded to the WebSocket client"""

    @abstractmethod
    async def close(self, code: int = 1000, reason: Optional[str] = None) -> None:
        """Close the WebSocket with the passed code and reason"""

    @abstractmethod
    async def handle_request(self) -> Any:
        """Handle the request this instance was created for"""

    async def handle(self) -> Any:
        return await self.handle_request()

    async def handle_message(
        self,
        message: OperationMessage,
    ) -> None:
        message_type = message["type"]

        if message_type == GQL_CONNECTION_INIT:
            await self.handle_connection_init(message)
        elif message_type == GQL_CONNECTION_TERMINATE:
            await self.handle_connection_terminate(message)
        elif message_type == GQL_START:
            await self.handle_start(message)
        elif message_type == GQL_STOP:
            await self.handle_stop(message)

    async def handle_connection_init(self, message: OperationMessage) -> None:
        data: OperationMessage = {"type": GQL_CONNECTION_ACK}
        await self.send_json(data)

        if self.keep_alive:
            keep_alive_handler = self.handle_keep_alive()
            self.keep_alive_task = asyncio.create_task(keep_alive_handler)

    async def handle_connection_terminate(self, message: OperationMessage) -> None:
        await self.close()

    async def handle_start(self, message: OperationMessage) -> None:
        operation_id = message["id"]
        payload = cast(StartPayload, message["payload"])
        query = payload["query"]
        operation_name = payload.get("operationName")
        variables = payload.get("variables")

        context = await self.get_context()
        root_value = await self.get_root_value()

        if self.debug:
            pretty_print_graphql_operation(operation_name, query, variables)

        try:
            result_source = await self.schema.subscribe(
                query=query,
                variable_values=variables,
                operation_name=operation_name,
                context_value=context,
                root_value=root_value,
            )
        except GraphQLError as error:
            error_payload = format_graphql_error(error)
            await self.send_message(GQL_ERROR, operation_id, error_payload)
            self.schema.process_errors([error])
            return

        if isinstance(result_source, GraphQLExecutionResult):
            assert result_source.errors
            error_payload = format_graphql_error(result_source.errors[0])
            await self.send_message(GQL_ERROR, operation_id, error_payload)
            self.schema.process_errors(result_source.errors)
            return

        self.subscriptions[operation_id] = result_source
        result_handler = self.handle_async_results(result_source, operation_id)
        self.tasks[operation_id] = asyncio.create_task(result_handler)

    async def handle_stop(self, message: OperationMessage) -> None:
        operation_id = message["id"]
        await self.cleanup_operation(operation_id)

    async def handle_keep_alive(self) -> None:
        while True:
            data: OperationMessage = {"type": GQL_CONNECTION_KEEP_ALIVE}
            await self.send_json(data)
            await asyncio.sleep(self.keep_alive_interval)

    async def handle_async_results(
        self,
        result_source: AsyncGenerator,
        operation_id: str,
    ) -> None:
        try:
            async for result in result_source:
                payload = {"data": result.data}
                if result.errors:
                    payload["errors"] = [
                        format_graphql_error(err) for err in result.errors
                    ]
                await self.send_message(GQL_DATA, operation_id, payload)
                # log errors after send_message to prevent potential
                # slowdown of sending result
                if result.errors:
                    self.schema.process_errors(result.errors)
        except asyncio.CancelledError:
            # CancelledErrors are expected during task cleanup.
            pass
        except Exception as error:
            # GraphQLErrors are handled by graphql-core and included in the
            # ExecutionResult
            error = GraphQLError(str(error), original_error=error)
            await self.send_message(
                GQL_DATA,
                operation_id,
                {"data": None, "errors": [format_graphql_error(error)]},
            )
            self.schema.process_errors([error])

        await self.send_message(GQL_COMPLETE, operation_id, None)

    async def cleanup_operation(self, operation_id: str) -> None:
        await self.subscriptions[operation_id].aclose()
        del self.subscriptions[operation_id]

        self.tasks[operation_id].cancel()
        with suppress(BaseException):
            await self.tasks[operation_id]
        del self.tasks[operation_id]

    async def send_message(
        self,
        type_: str,
        operation_id: str,
        payload: Optional[OperationMessagePayload] = None,
    ) -> None:
        data: OperationMessage = {"type": type_, "id": operation_id}
        if payload is not None:
            data["payload"] = payload
        await self.send_json(data)
