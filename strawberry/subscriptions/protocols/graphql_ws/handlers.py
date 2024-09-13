from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from contextlib import suppress
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Awaitable,
    Dict,
    Optional,
    cast,
)

from strawberry.subscriptions.protocols.graphql_ws import (
    GQL_COMPLETE,
    GQL_CONNECTION_ACK,
    GQL_CONNECTION_ERROR,
    GQL_CONNECTION_INIT,
    GQL_CONNECTION_KEEP_ALIVE,
    GQL_CONNECTION_TERMINATE,
    GQL_DATA,
    GQL_ERROR,
    GQL_START,
    GQL_STOP,
)
from strawberry.types.execution import ExecutionResult, PreExecutionError
from strawberry.utils.debug import pretty_print_graphql_operation

if TYPE_CHECKING:
    from strawberry.schema import BaseSchema
    from strawberry.schema.subscribe import SubscriptionResult
    from strawberry.subscriptions.protocols.graphql_ws.types import (
        ConnectionInitPayload,
        DataPayload,
        OperationMessage,
        OperationMessagePayload,
        StartPayload,
    )


class BaseGraphQLWSHandler(ABC):
    def __init__(
        self,
        schema: BaseSchema,
        debug: bool,
        keep_alive: bool,
        keep_alive_interval: float,
    ) -> None:
        self.schema = schema
        self.debug = debug
        self.keep_alive = keep_alive
        self.keep_alive_interval = keep_alive_interval
        self.keep_alive_task: Optional[asyncio.Task] = None
        self.subscriptions: Dict[str, AsyncGenerator] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        self.connection_params: Optional[ConnectionInitPayload] = None

    @abstractmethod
    async def get_context(self) -> Any:
        """Return the operations context."""

    @abstractmethod
    async def get_root_value(self) -> Any:
        """Return the schemas root value."""

    @abstractmethod
    async def send_json(self, data: OperationMessage) -> None:
        """Send the data JSON encoded to the WebSocket client."""

    @abstractmethod
    async def close(self, code: int = 1000, reason: Optional[str] = None) -> None:
        """Close the WebSocket with the passed code and reason."""

    @abstractmethod
    async def handle_request(self) -> Any:
        """Handle the request this instance was created for."""

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
        payload = message.get("payload")
        if payload is not None and not isinstance(payload, dict):
            error_message: OperationMessage = {"type": GQL_CONNECTION_ERROR}
            await self.send_json(error_message)
            await self.close()
            return

        payload = cast(Optional["ConnectionInitPayload"], payload)
        self.connection_params = payload

        acknowledge_message: OperationMessage = {"type": GQL_CONNECTION_ACK}
        await self.send_json(acknowledge_message)

        if self.keep_alive:
            keep_alive_handler = self.handle_keep_alive()
            self.keep_alive_task = asyncio.create_task(keep_alive_handler)

    async def handle_connection_terminate(self, message: OperationMessage) -> None:
        await self.close()

    async def handle_start(self, message: OperationMessage) -> None:
        operation_id = message["id"]
        payload = cast("StartPayload", message["payload"])
        query = payload["query"]
        operation_name = payload.get("operationName")
        variables = payload.get("variables")

        context = await self.get_context()
        if isinstance(context, dict):
            context["connection_params"] = self.connection_params
        root_value = await self.get_root_value()

        if self.debug:
            pretty_print_graphql_operation(operation_name, query, variables)

        result_source = self.schema.subscribe(
            query=query,
            variable_values=variables,
            operation_name=operation_name,
            context_value=context,
            root_value=root_value,
        )

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
        result_source: Awaitable[SubscriptionResult],
        operation_id: str,
    ) -> None:
        try:
            agen_or_err = await result_source
            if isinstance(agen_or_err, PreExecutionError):
                assert agen_or_err.errors
                error_payload = agen_or_err.errors[0].formatted
                await self.send_message(GQL_ERROR, operation_id, error_payload)
            else:
                self.subscriptions[operation_id] = agen_or_err
                async for result in agen_or_err:
                    await self.send_data(result, operation_id)
                await self.send_message(GQL_COMPLETE, operation_id, None)
        except asyncio.CancelledError:
            await self.send_message(GQL_COMPLETE, operation_id, None)

    async def cleanup_operation(self, operation_id: str) -> None:
        if operation_id in self.subscriptions:
            with suppress(RuntimeError):
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

    async def send_data(
        self, execution_result: ExecutionResult, operation_id: str
    ) -> None:
        payload: DataPayload = {"data": execution_result.data}
        if execution_result.errors:
            payload["errors"] = [err.formatted for err in execution_result.errors]
        if execution_result.extensions:
            payload["extensions"] = execution_result.extensions
        await self.send_message(GQL_DATA, operation_id, payload)


__all__ = ["BaseGraphQLWSHandler"]
