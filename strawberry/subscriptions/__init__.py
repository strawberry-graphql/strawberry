from typing_extensions import Literal

GRAPHQL_TRANSPORT_WS_PROTOCOL = "graphql-transport-ws"
GRAPHQL_WS_PROTOCOL = "graphql-ws"

SubscriptionProtocolType = Literal[GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL]

# Code 4406 is "Subprotocol not acceptable"
WS_4406_PROTOCOL_NOT_ACCEPTABLE = 4406
