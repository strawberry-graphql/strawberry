Release type: patch

This release fixes two security vulnerabilities in the WebSocket subscription
handlers (CVE-2026-35526, CVE-2026-35523).

**CVE-2026-35526 - Authentication bypass in `graphql-ws`**: The legacy
`graphql-ws` protocol handler didn't verify that the `connection_init`
handshake was completed before accepting `start` messages, allowing clients
to bypass any authentication logic in `on_ws_connect`. The connection is now
closed with `4401 Unauthorized` if the handshake hasn't been completed.

**CVE-2026-35523 - Unbounded subscriptions per connection**: Both WebSocket
protocol handlers allowed unlimited concurrent subscriptions on a single
connection, making it possible for a malicious client to exhaust server
resources. A new `max_subscriptions_per_connection` parameter has been added
to all views (default: `100`). Set it to `None` to disable the limit.

Example:

```python
import strawberry
from strawberry.fastapi import GraphQLRouter

schema = strawberry.Schema(query=Query, subscription=Subscription)

# default is 100, set to None to disable the limit
graphql_app = GraphQLRouter(schema, max_subscriptions_per_connection=50)
```
