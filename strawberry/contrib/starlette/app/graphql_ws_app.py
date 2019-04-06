import functools
import typing

# from graphql.error import GraphQLError, format_error as format_graphql_error
from graphql.language import parse
from graphql.subscription import subscribe
from starlette.types import ASGIInstance, Receive, Scope, Send
from starlette.websockets import WebSocket

from .base import BaseApp


class GraphQLSubscriptionApp(BaseApp):
    def __call__(self, scope: Scope) -> ASGIInstance:
        return functools.partial(self.asgi, scope=scope)

    async def execute(self, query, variables=None, context=None, operation_name=None):
        return await subscribe(
            self.schema,
            parse(query),
            variable_values=variables,
            operation_name=operation_name,
            context_value=context,
        )

    async def _send_message(
        self,
        websocket: WebSocket,
        type_: str,
        payload: typing.Any = None,
        id_: str = None,
    ) -> None:
        data = {"type": type_}

        if id_ is not None:
            data["id"] = id_

        if payload is not None:
            data["payload"] = payload

        return await websocket.send_json(data)

    async def asgi(self, receive: Receive, send: Send, scope: Scope) -> None:
        assert scope["type"] == "websocket"

        websocket = WebSocket(scope, receive=receive, send=send)
        await websocket.accept(subprotocol="graphql-ws")
        await self._send_message(websocket, "connection_ack")

        # TODO: we should check that this is a proper connection init message
        await websocket.receive_json()
        data = await websocket.receive_json()

        id_ = data.get("id", "1")
        payload = data.get("payload", {})

        data = await self.execute(
            payload["query"],
            payload["variables"],
            operation_name=payload["operationName"],
        )

        async for result in data:
            # TODO: send errors if any

            await self._send_message(websocket, "data", {"data": result.data}, id_)

        await self._send_message(websocket, "complete")
        await websocket.close()
