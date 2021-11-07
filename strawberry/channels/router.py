"""GraphQLWebSocketRouter

This is a simple router class that might be better placed as part of Channels itself.
It's a simple "SubProtocolRouter" that selects the websocket subprotocol based
on preferences and client support. Then it hands off to the appropriate consumer.
"""
from datetime import timedelta
from typing import Any, Optional, Sequence, Union

from django.http import HttpRequest, HttpResponse
from django.urls import re_path

from channels.generic.websocket import (
    AsyncJsonWebsocketConsumer,
    AsyncWebsocketConsumer,
)
from channels.routing import ProtocolTypeRouter, URLRouter
from strawberry.http import GraphQLHTTPResponse, process_result
from strawberry.schema import BaseSchema
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL
from strawberry.types import ExecutionResult

from .context import StrawberryChannelsContext
from .handlers.graphql_transport_ws_handler import GraphQLTransportWSHandler
from .handlers.graphql_ws_handler import GraphQLWSHandler
from .handlers.http_handler import GraphQLHTTPConsumer


class GraphQLWSConsumer(AsyncJsonWebsocketConsumer):
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
        re_path("^graphql", GraphQLHTTPConsumer(schema=schema)),
        re_path("^", get_asgi_application()),
      "websocket": URLRouter([
        re_path("^ws/graphql", GraphQLWSConsumer(schema=schema))
      ]),
    })
    """

    graphql_transport_ws_handler_class = GraphQLTransportWSHandler
    graphql_ws_handler_class = GraphQLWSHandler
    _handler: Union[GraphQLWSHandler, GraphQLTransportWSHandler]

    def __init__(
        self,
        schema: BaseSchema,
        graphiql: bool = True,
        keep_alive: bool = False,
        keep_alive_interval: float = 1,
        debug: bool = False,
        subscription_protocols=(GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL),
        connection_init_wait_timeout: timedelta = None,
    ):
        if connection_init_wait_timeout is None:
            connection_init_wait_timeout = timedelta(minutes=1)
        self.connection_init_wait_timeout = connection_init_wait_timeout
        self.schema = schema
        self.graphiql = graphiql
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

    async def connect(self):
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

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        try:
            await super().receive(text_data=text_data, bytes_data=bytes_data, **kwargs)
        except ValueError:
            await self._handler.handle_invalid_message(
                "WebSocket message type must be text"
            )

    async def receive_json(self, content, **kwargs):
        await self._handler.handle_message(content)

    async def disconnect(self, code):
        await self._handler.handle_disconnect(code)

    async def get_root_value(
        self, request: HttpRequest = None, consumer: AsyncWebsocketConsumer = None
    ) -> Optional[Any]:
        return None

    async def get_context(
        self,
        request: Union[HttpRequest, AsyncJsonWebsocketConsumer] = None,
        response: Optional[HttpResponse] = None,
    ) -> Optional[Any]:
        return StrawberryChannelsContext(request=request or self, response=response)

    async def process_result(
        self,
        request: HttpRequest,
        result: ExecutionResult,
        consumer: AsyncWebsocketConsumer = None,
    ) -> GraphQLHTTPResponse:
        return process_result(result)


class GraphQLProtocolTypeRouter(ProtocolTypeRouter):
    """
    Convenience class to set up GraphQL on both HTTP and Websocket, optionally with a
    Django application for all other HTTP routes:
    ```
    from strawberry.channels import GraphQLProtocolTypeRouter
    from django.core.asgi import get_asgi_application

    django_asgi = get_asgi_application()

    from myapi import schema

    application = GraphQLProtocolTypeRouter(
        schema,
        django_application=django_asgi,
    )
    ```
    This will route all requests to /graphql on either HTTP or websockets to us,
    and everything else to the Django application.
    """

    def __init__(
        self, schema: BaseSchema, django_application=None, url_pattern="^graph"
    ):
        http_urls = [re_path(url_pattern, GraphQLHTTPConsumer.as_asgi(schema=schema))]
        if django_application is not None:
            http_urls.append(re_path("^", django_application))

        super().__init__(
            {
                "http": URLRouter(http_urls),
                "websocket": URLRouter(
                    [
                        re_path(url_pattern, GraphQLWSConsumer.as_asgi(schema=schema)),
                    ]
                ),
            }
        )
