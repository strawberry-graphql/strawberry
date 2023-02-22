from __future__ import annotations

import dataclasses
import uuid
from typing import TYPE_CHECKING, AsyncIterator, Dict, List, Optional, Tuple, Union

from graphql import GraphQLError

from channels.testing.websocket import WebsocketCommunicator
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL
from strawberry.subscriptions.protocols.graphql_transport_ws.types import (
    ConnectionAckMessage,
    ConnectionInitMessage,
    ErrorMessage,
    NextMessage,
    SubscribeMessage,
    SubscribeMessagePayload,
)
from strawberry.subscriptions.protocols.graphql_ws import (
    GQL_CONNECTION_ACK,
    GQL_CONNECTION_INIT,
    GQL_START,
)
from strawberry.types import ExecutionResult

if TYPE_CHECKING:
    from asgiref.typing import ASGIApplication


class GraphQLWebsocketCommunicator(WebsocketCommunicator):
    """
    Usage:
    ```python
    import pytest
    from strawberry.channels.testing import GraphQLWebsocketCommunicator
    from myapp.asgi import application


    @pytest.fixture
    async def gql_communicator():
        async with GraphQLWebsocketCommunicator(application, path="/graphql") as client:
            yield client


    async def test_subscribe_echo(gql_communicator):
        async for res in gql_communicator.subscribe(
            query='subscription { echo(message: "Hi") }'
        ):
            assert res.data == {"echo": "Hi"}
    ```
    """

    def __init__(
        self,
        application: ASGIApplication,
        path: str,
        headers: Optional[List[Tuple[bytes, bytes]]] = None,
        protocol: str = GRAPHQL_TRANSPORT_WS_PROTOCOL,
        **kwargs,
    ):
        """

        Args:
            application: Your asgi application that encapsulates the strawberry schema.
            path: the url endpoint for the schema.
            protocol: currently this supports `graphql-transport-ws` only.
        """
        self.protocol = protocol
        subprotocols = kwargs.get("subprotocols", [])
        subprotocols.append(protocol)
        super().__init__(application, path, headers, subprotocols=subprotocols)

    async def __aenter__(self) -> GraphQLWebsocketCommunicator:
        await self.gql_init()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.disconnect()

    async def gql_init(self):
        res = await self.connect()
        if self.protocol == GRAPHQL_TRANSPORT_WS_PROTOCOL:
            assert res == (True, GRAPHQL_TRANSPORT_WS_PROTOCOL)
            await self.send_json_to(ConnectionInitMessage().as_dict())
            response = await self.receive_json_from()
            assert response == ConnectionAckMessage().as_dict()
        else:
            assert res == (True, GRAPHQL_WS_PROTOCOL)
            await self.send_json_to({"type": GQL_CONNECTION_INIT})
            response = await self.receive_json_from()
            assert response["type"] == GQL_CONNECTION_ACK

    async def subscribe(
        self, query: str, variables: Optional[Dict] = None
    ) -> Union[ExecutionResult, AsyncIterator[ExecutionResult]]:
        id_ = uuid.uuid4().hex
        sub_payload = SubscribeMessagePayload(query=query, variables=variables)
        if self.protocol == GRAPHQL_TRANSPORT_WS_PROTOCOL:
            await self.send_json_to(
                SubscribeMessage(
                    id=id_,
                    payload=sub_payload,
                ).as_dict()
            )
        else:
            await self.send_json_to(
                {
                    "type": GQL_START,
                    "id": id_,
                    "payload": dataclasses.asdict(sub_payload),
                }
            )
        while True:
            response = await self.receive_json_from(timeout=5)
            message_type = response["type"]
            if message_type == NextMessage.type:
                payload = NextMessage(**response).payload
                ret = ExecutionResult(None, None)
                for field in dataclasses.fields(ExecutionResult):
                    setattr(ret, field.name, payload.get(field.name, None))
                    yield ret
            elif message_type == ErrorMessage.type:
                error_payload = ErrorMessage(**response).payload
                yield ExecutionResult(
                    data=None,
                    errors=[
                        GraphQLError(
                            message=message["message"],
                            extensions=message.get("extensions", None),
                        )
                        for message in error_payload
                    ],
                )
            else:
                return
