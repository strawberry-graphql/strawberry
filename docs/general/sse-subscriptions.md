---
title: SSE Subscriptions (GraphQL-SSE)
---

# SSE Subscriptions (GraphQL-SSE)

Strawberry supports subscriptions over Server-Sent Events (SSE) following the
[GraphQL over SSE protocol](https://github.com/enisdenjo/graphql-sse/blob/master/PROTOCOL.md)
(distinct connections mode). This provides a lightweight alternative to
WebSocket subscriptions that works over standard HTTP connections.

## How it works

When a client sends a GraphQL subscription request with
`Accept: text/event-stream`, Strawberry responds with an SSE stream instead of
using WebSocket or multipart responses. The server streams results using
standard SSE event format:

- **`next` events** contain execution results as JSON in the `data` field
- **`complete` event** signals the end of the subscription stream
- **SSE comments** (`:` lines) are used as heartbeat keepalive signals

## Support

SSE subscriptions are supported out of the box in the following HTTP frameworks:

- ASGI (Starlette)
- FastAPI
- AioHTTP
- Quart
- Django (only in the Async view)
- Litestar
- Sanic

## Usage

SSE subscriptions are automatically enabled when using
`@strawberry.subscription`. No additional server configuration is required. The
client needs to send the `Accept: text/event-stream` header with its
subscription request.

### Example subscription

```python
import asyncio
from collections.abc import AsyncGenerator

import strawberry


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def count(self, target: int = 10) -> AsyncGenerator[int, None]:
        for i in range(target):
            yield i
            await asyncio.sleep(1)
```

### Client-side usage

#### Using the `graphql-sse` JavaScript client

The recommended client library is
[graphql-sse](https://github.com/enisdenjo/graphql-sse):

```javascript
import { createClient } from "graphql-sse";

const client = createClient({
  url: "http://localhost:8000/graphql",
});

const subscription = client.iterate({
  query: "subscription { count(target: 10) }",
});

for await (const result of subscription) {
  console.log(result);
}
```

#### Using the native EventSource API

For basic use cases with GET requests, you can use the browser's built-in
`EventSource`. Note that `EventSource` does not support custom headers or POST
requests — for those, use the `graphql-sse` client library.

```javascript
const eventSource = new EventSource(
  "/graphql?query=subscription { count(target: 10) }",
);

eventSource.addEventListener("next", (event) => {
  const data = JSON.parse(event.data);
  console.log(data.payload);
});

eventSource.addEventListener("complete", () => {
  eventSource.close();
});
```

## SSE event format

The response uses `Content-Type: text/event-stream` and follows the standard SSE
format:

```
event: next
data: {"payload": {"data": {"count": 0}}}

event: next
data: {"payload": {"data": {"count": 1}}}

event: complete
data:
```

Heartbeat messages are sent as SSE comments every 5 seconds to prevent
connection timeouts:

```
:

```

## Extensions

Schema extensions work with SSE subscriptions just as they do with regular GraphQL
operations. Each `next` event triggers the extension's `get_results()` method,
allowing extensions to inject additional fields into the response payload.

```python
import strawberry
from strawberry.extensions import SchemaExtension


class TracingExtension(SchemaExtension):
    async def get_results(self) -> dict:
        return {"extension": {"traceId": "abc123"}}


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def count(self, target: int = 10) -> AsyncGenerator[int, None]:
        for i in range(target):
            yield i


schema = strawberry.Schema(
    Subscription,
    extensions=[TracingExtension],
)
```

Each concurrent subscription receives its own extension instance, so state is
isolated between subscriptions. Extension lifecycle hooks (`on_operation`,
`on_execute`) are called once per subscription start, while `get_results` is
called for each yielded value.

For more details on creating custom extensions, see the
[custom extensions guide](../guides/custom-extensions.md).

## Comparison with other subscription transports

| Feature            | WebSocket    | Multipart HTTP | SSE           |
| ------------------ | ------------ | -------------- | ------------- |
| Protocol           | `wss://`     | HTTP           | HTTP          |
| Connection upgrade | Yes (101)    | No             | No            |
| Bidirectional      | Yes          | No             | No            |
| Proxy-friendly     | Sometimes    | Yes            | Yes           |
| Browser support    | Good         | Limited        | Excellent     |
| Client library     | `graphql-ws` | Apollo Client  | `graphql-sse` |
