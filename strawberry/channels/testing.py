import dataclasses
import uuid
from typing import AsyncIterator, Dict, Optional, Union

from channels.testing.websocket import WebsocketCommunicator
from strawberry.exceptions import GraphQLError
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL
from strawberry.subscriptions.protocols.graphql_transport_ws.types import (
    ConnectionAckMessage,
    ConnectionInitMessage,
    SubscribeMessage,
    SubscribeMessagePayload,
)
from strawberry.types import ExecutionResult


class GqlWsCommunicator(WebsocketCommunicator):
    """exposes API like strawberry.Schema"""

    def __init__(self, application, path, headers=None, subprotocols=None):
        subprotocols = (
            subprotocols
            if subprotocols
            else [
                GRAPHQL_TRANSPORT_WS_PROTOCOL,
            ]
        )
        super().__init__(application, path, headers, subprotocols)

    async def gql_init(self):
        res = await self.connect()
        assert res == (True, GRAPHQL_TRANSPORT_WS_PROTOCOL)
        await self.send_json_to(ConnectionInitMessage().as_dict())
        response = await self.receive_json_from()
        assert response == ConnectionAckMessage().as_dict()

    async def subscribe(
        self, query: str, variables: Optional[Dict] = None
    ) -> Union[ExecutionResult, AsyncIterator[ExecutionResult]]:
        id_ = uuid.uuid4().hex
        await self.send_json_to(
            SubscribeMessage(
                id=id_,
                payload=SubscribeMessagePayload(query=query, variables=variables),
            ).as_dict()
        )
        while True:
            response = await self.receive_json_from(timeout=5)
            message_type = response["type"]
            if message_type == "next":
                payload = response["payload"]
                ret = ExecutionResult(None, None)
                for field in dataclasses.fields(ExecutionResult):
                    setattr(ret, field.name, payload.get(field.name, None))
                    yield ret
            elif message_type == "error":
                raise RuntimeError(
                    *[
                        GraphQLError(
                            message=message["message"],
                            extensions=message.get("extensions", None),
                        )
                        for message in response["payload"]
                    ]
                )
            else:
                return
