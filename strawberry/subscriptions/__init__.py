from typing_extensions import Literal

GRAPHQL_TRANSPORT_WS_PROTOCOL = "graphql-transport-ws"
GRAPHQL_WS_PROTOCOL = "graphql-ws"

SubscriptionProtocolType = Literal[  #  type: ignore
    GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL  #  type: ignore
]
