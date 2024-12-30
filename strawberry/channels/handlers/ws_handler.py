from __future__ import annotations

import asyncio
import datetime
import json
from typing import (
    TYPE_CHECKING,
    Optional,
    TypedDict,
    Union,
)
from typing_extensions import TypeGuard

from strawberry.http.async_base_view import AsyncBaseHTTPView, AsyncWebSocketAdapter
from strawberry.http.exceptions import NonJsonMessageReceived, NonTextMessageReceived
from strawberry.http.typevars import Context, RootValue
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL

from .base import ChannelsWSConsumer

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Mapping

    from strawberry.http import GraphQLHTTPResponse
    from strawberry.schema import BaseSchema


class ChannelsWebSocketAdapter(AsyncWebSocketAdapter):
    def __init__(
        self,
        view: AsyncBaseHTTPView,
        request: GraphQLWSConsumer,
        response: GraphQLWSConsumer,
    ) -> None:
        super().__init__(view)
        self.ws_consumer = response

    async def iter_json(
        self, *, ignore_parsing_errors: bool = False
    ) -> AsyncGenerator[object, None]:
        while True:
            message = await self.ws_consumer.message_queue.get()

            if message["disconnected"]:
                break

            if message["message"] is None:
                raise NonTextMessageReceived

            try:
                yield self.view.decode_json(message["message"])
            except json.JSONDecodeError as e:
                if not ignore_parsing_errors:
                    raise NonJsonMessageReceived from e

    async def send_json(self, message: Mapping[str, object]) -> None:
        serialized_message = self.view.encode_json(message)
        await self.ws_consumer.send(serialized_message)

    async def close(self, code: int, reason: str) -> None:
        await self.ws_consumer.close(code=code, reason=reason)


class MessageQueueData(TypedDict):
    message: Union[str, None]
    disconnected: bool


class GraphQLWSConsumer(
    ChannelsWSConsumer,
    AsyncBaseHTTPView[
        "GraphQLWSConsumer",
        "GraphQLWSConsumer",
        "GraphQLWSConsumer",
        "GraphQLWSConsumer",
        "GraphQLWSConsumer",
        Context,
        RootValue,
    ],
):
    """A channels websocket consumer for GraphQL.

    This handles the connections, then hands off to the appropriate
    handler based on the subprotocol.

    To use this, place it in your ProtocolTypeRouter for your channels project, e.g:

    ```
    from strawberry.channels import GraphQLHttpRouter
    from channels.routing import ProtocolTypeRouter
    from django.core.asgi import get_asgi_application

    application = ProtocolTypeRouter({
        "http": URLRouter([
            re_path("^graphql", GraphQLHTTPRouter(schema=schema)),
            re_path("^", get_asgi_application()),
        ]),
        "websocket": URLRouter([
            re_path("^ws/graphql", GraphQLWebSocketRouter(schema=schema)),
        ]),
    })
    ```
    """

    websocket_adapter_class = ChannelsWebSocketAdapter

    def __init__(
        self,
        schema: BaseSchema,
        keep_alive: bool = False,
        keep_alive_interval: float = 1,
        debug: bool = False,
        subscription_protocols: tuple[str, str] = (
            GRAPHQL_TRANSPORT_WS_PROTOCOL,
            GRAPHQL_WS_PROTOCOL,
        ),
        connection_init_wait_timeout: Optional[datetime.timedelta] = None,
    ) -> None:
        if connection_init_wait_timeout is None:
            connection_init_wait_timeout = datetime.timedelta(minutes=1)
        self.connection_init_wait_timeout = connection_init_wait_timeout
        self.schema = schema
        self.keep_alive = keep_alive
        self.keep_alive_interval = keep_alive_interval
        self.debug = debug
        self.protocols = subscription_protocols
        self.message_queue: asyncio.Queue[MessageQueueData] = asyncio.Queue()
        self.run_task: Optional[asyncio.Task] = None

        super().__init__()

    async def connect(self) -> None:
        self.run_task = asyncio.create_task(self.run(self))

    async def receive(
        self, text_data: Optional[str] = None, bytes_data: Optional[bytes] = None
    ) -> None:
        if text_data:
            self.message_queue.put_nowait({"message": text_data, "disconnected": False})
        else:
            self.message_queue.put_nowait({"message": None, "disconnected": False})

    async def disconnect(self, code: int) -> None:
        self.message_queue.put_nowait({"message": None, "disconnected": True})
        assert self.run_task
        await self.run_task

    async def get_root_value(self, request: GraphQLWSConsumer) -> Optional[RootValue]:
        return None

    async def get_context(
        self, request: GraphQLWSConsumer, response: GraphQLWSConsumer
    ) -> Context:
        return {
            "request": request,
            "ws": request,
        }  # type: ignore

    @property
    def allow_queries_via_get(self) -> bool:
        return False

    async def get_sub_response(self, request: GraphQLWSConsumer) -> GraphQLWSConsumer:
        raise NotImplementedError

    def create_response(
        self, response_data: GraphQLHTTPResponse, sub_response: GraphQLWSConsumer
    ) -> GraphQLWSConsumer:
        raise NotImplementedError

    async def render_graphql_ide(self, request: GraphQLWSConsumer) -> GraphQLWSConsumer:
        raise NotImplementedError

    def is_websocket_request(
        self, request: GraphQLWSConsumer
    ) -> TypeGuard[GraphQLWSConsumer]:
        return True

    async def pick_websocket_subprotocol(
        self, request: GraphQLWSConsumer
    ) -> Optional[str]:
        protocols = request.scope["subprotocols"]
        intersection = set(protocols) & set(self.protocols)
        sorted_intersection = sorted(intersection, key=protocols.index)
        return next(iter(sorted_intersection), None)

    async def create_websocket_response(
        self, request: GraphQLWSConsumer, subprotocol: Optional[str]
    ) -> GraphQLWSConsumer:
        await request.accept(subprotocol=subprotocol)
        return request


__all__ = ["GraphQLWSConsumer"]
