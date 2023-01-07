from enum import Enum
from typing import Literal


class SubscriptionProtocol(Enum):
    GRAPHQL_TRANSPORT_WS = "graphql-transport-ws"
    GRAPHQL_WS = "graphql-ws"


SubscriptionProtocolType = Literal[
    SubscriptionProtocol.GRAPHQL_TRANSPORT_WS,
    SubscriptionProtocol.GRAPHQL_WS,
]
