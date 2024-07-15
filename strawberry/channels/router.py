"""GraphQLWebSocketRouter.

This is a simple router class that might be better placed as part of Channels itself.
It's a simple "SubProtocolRouter" that selects the websocket subprotocol based
on preferences and client support. Then it hands off to the appropriate consumer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from django.urls import re_path

from channels.routing import ProtocolTypeRouter, URLRouter

from .handlers.http_handler import GraphQLHTTPConsumer
from .handlers.ws_handler import GraphQLWSConsumer

if TYPE_CHECKING:
    from strawberry.schema import BaseSchema


class GraphQLProtocolTypeRouter(ProtocolTypeRouter):
    """HTTP and Websocket GraphQL type router.

    Convenience class to set up GraphQL on both HTTP and Websocket,
    optionally with a Django application for all other HTTP routes.

    ```python
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
        self,
        schema: BaseSchema,
        django_application: Optional[str] = None,
        url_pattern: str = "^graphql",
    ) -> None:
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


__all__ = ["GraphQLProtocolTypeRouter"]
