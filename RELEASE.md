---
release type: minor
---

This release adds support for GraphQL subscriptions over Server-Sent Events
(SSE), following the
[GraphQL over SSE](https://github.com/enisdenjo/graphql-sse/blob/master/PROTOCOL.md)
protocol in "distinct connections mode".

SSE is opt-in. Enable it by including `GRAPHQL_SSE_PROTOCOL` in your
integration's `subscription_protocols`:

```python
from strawberry.asgi import GraphQL
from strawberry.subscriptions import (
    GRAPHQL_SSE_PROTOCOL,
    GRAPHQL_TRANSPORT_WS_PROTOCOL,
    GRAPHQL_WS_PROTOCOL,
)

app = GraphQL(
    schema,
    subscription_protocols=[
        GRAPHQL_TRANSPORT_WS_PROTOCOL,
        GRAPHQL_WS_PROTOCOL,
        GRAPHQL_SSE_PROTOCOL,
    ],
)
```

Clients request a stream with `Accept: text/event-stream`. Queries, mutations,
subscriptions, and `@defer`/`@stream` are all supported on the async
streaming-capable integrations (ASGI, FastAPI, AIOHTTP, Litestar, Quart, Sanic,
async Django, and async Channels). See the
[SSE subscriptions docs](https://strawberry.rocks/docs/general/subscriptions#using-sse-subscriptions)
for client setup, reconnection, and deployment notes (prefer HTTP/2).

**Breaking change: multipart subscriptions are now opt-in.** Streaming
transports are selected from `subscription_protocols`, so multipart
subscriptions — previously served for any `Accept: multipart/mixed` request —
now require `MULTIPART_SUBSCRIPTION_PROTOCOL` to be listed there explicitly.
