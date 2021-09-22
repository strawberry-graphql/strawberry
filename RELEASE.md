This release adds support for the `graphql-transport-ws` GraphQL over WebSocket
protocol. Previously Strawberry only supported the legacy `graphql-ws` protocol.

Developers can decide which protocols they want to accept. The following example shows
how to do so using the ASGI integration. Take a look at our GraphQL subscription
documentation to learn more.

```python
from strawberry.asgi import GraphQL
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL
from api.schema import schema


app = GraphQL(schema, protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL])
```
