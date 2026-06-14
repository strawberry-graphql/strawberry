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

Clients then request a stream by sending a normal GraphQL request with
`Accept: text/event-stream`. Strawberry sends each result as a `next` event and
a `complete` event when the operation finishes, with comment heartbeats on idle
streams. Queries, mutations, subscriptions, and `@defer`/`@stream` are all
supported. It works on the async streaming-capable integrations (ASGI, FastAPI,
AIOHTTP, Litestar, Quart, Sanic, async Django, and async Channels).

SSE uses normal HTTP requests, so reconnection is handled in userland: read the
client's `Last-Event-ID` header from the request (available in the context) and
resume from it in your resolver. Strawberry never buffers or replays results
itself.

Enabling SSE no longer leaks `graphql-sse` into WebSocket subprotocol
negotiation: the WebSocket handshake only advertises the WebSocket subprotocols
from `subscription_protocols`.

Multipart subscriptions are explicit too: include
`MULTIPART_SUBSCRIPTION_PROTOCOL` in `subscription_protocols` if you use that
transport.
