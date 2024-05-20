from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any, Optional, Sequence, Tuple, Union

from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL

from .base import ChannelsConsumer, ChannelsWSConsumer
from .graphql_transport_ws_handler import GraphQLTransportWSHandler
from .graphql_ws_handler import GraphQLWSHandler

if TYPE_CHECKING:
    from strawberry.http.typevars import Context, RootValue
    from strawberry.schema import BaseSchema


class GraphQLWSConsumer(ChannelsWSConsumer):
    """A channels websocket consumer for GraphQL

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

    graphql_transport_ws_handler_class = GraphQLTransportWSHandler
    graphql_ws_handler_class = GraphQLWSHandler
    _handler: Union[GraphQLWSHandler, GraphQLTransportWSHandler]

    def __init__(
        self,
        schema: BaseSchema,
        keep_alive: bool = False,
        keep_alive_interval: float = 1,
        debug: bool = False,
        subscription_protocols: Tuple[str, str] = (
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

        super().__init__()

    def pick_preferred_protocol(
        self, accepted_subprotocols: Sequence[str]
    ) -> Optional[str]:
        intersection = set(accepted_subprotocols) & set(self.protocols)
        sorted_intersection = sorted(intersection, key=accepted_subprotocols.index)
        return next(iter(sorted_intersection), None)

    async def connect(self) -> None:
        preferred_protocol = self.pick_preferred_protocol(self.scope["subprotocols"])

        if preferred_protocol == GRAPHQL_TRANSPORT_WS_PROTOCOL:
            self._handler = self.graphql_transport_ws_handler_class(
                schema=self.schema,
                debug=self.debug,
                connection_init_wait_timeout=self.connection_init_wait_timeout,
                get_context=self.get_context,
                get_root_value=self.get_root_value,
                ws=self,
            )
        elif preferred_protocol == GRAPHQL_WS_PROTOCOL:
            self._handler = self.graphql_ws_handler_class(
                schema=self.schema,
                debug=self.debug,
                keep_alive=self.keep_alive,
                keep_alive_interval=self.keep_alive_interval,
                get_context=self.get_context,
                get_root_value=self.get_root_value,
                ws=self,
            )
        else:
            # Subprotocol not acceptable
            return await self.close(code=4406)

        await self._handler.handle()
        return None

    async def receive(self, *args: str, **kwargs: Any) -> None:
        # Overriding this so that we can pass the errors to handle_invalid_message
        try:
            await super().receive(*args, **kwargs)
        except ValueError as e:
            await self._handler.handle_invalid_message(str(e))

    async def receive_json(self, content: Any, **kwargs: Any) -> None:
        await self._handler.handle_message(content)

    async def disconnect(self, code: int) -> None:
        await self._handler.handle_disconnect(code)

    async def get_root_value(self, request: ChannelsConsumer) -> Optional[RootValue]:
        return None

    async def get_context(
        self, request: ChannelsConsumer, connection_params: Any
    ) -> Context:
        return {
            "request": request,
            "connection_params": connection_params,
            "ws": request,
        }  # type: ignore
