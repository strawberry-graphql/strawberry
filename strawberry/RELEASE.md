Release Type: minor

# Release Notes: Initial GraphQL-SSE Support

## Overview

This release introduces native support for GraphQL-SSE (Server-Sent Events) for subscription transport in Strawberry GraphQL. This feature enables real-time subscription updates over HTTP using the SSE protocol, providing a more efficient and persistent connection compared to polling.

## What's New

### GraphQL-SSE Subscription Support

Strawberry now supports GraphQL-SSE as a subscription transport mechanism. This allows subscriptions to stream data over HTTP using Server-Sent Events (SSE), with full compatibility with the graphql-transport-ws subprotocol.

#### Supported HTTP Methods

- **GET**: SSE over GET requests for subscriptions
- **POST**: SSE over POST requests with JSON body

#### Response Formats

The implementation supports multiple response formats:

1. **SSE (text/event-stream)**: Streams individual events as they occur
2. **Multipart (multipart/mixed)**: Supports the graphql-transport-ws multipart format

## Example Usage

### Subscription Definition

```python
import strawberry
from strawberry.types import Info
from typing import AsyncGenerator

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def check(self, info: Info) -> AsyncGenerator[str, None]:
        while True:
            yield "Hello"
            await anyio.sleep(2.5)
```

### Client Usage

#### SSE with GET

```bash
curl -N -k -G 'https://localhost:8888/graphql' \
  -H 'Accept: text/event-stream' \
  --data-urlencode 'query=subscription { check }'
```

#### SSE with POST

```bash
curl -N -k -X POST https://localhost:8888/graphql \
  -H 'Accept: text/event-stream' \
  -H 'Content-Type: application/json' \
  --data-binary @- <<EOF
{
  "query": "subscription { check }"
}
EOF
```

#### Multipart with POST

```bash
curl -N -k -X POST https://localhost:8888/graphql \
  -H 'Accept: multipart/mixed; boundary=graphql; subscriptionSpec=1.0, application/json' \
  -H 'Content-Type: application/json' \
  --data-binary @- <<EOF
{
  "query": "subscription { check }"
}
EOF
```

## Response Format Changes

### Before (Legacy Format)

SSE responses used a legacy JSON format that didn't follow the graphql-transport-ws specification:

```
{"data":null,"errors":[{"message":"Cannot return null for non-nullable field Subscription.check","locations":[{"line":1,"column":16}],"path":["check"]}]}
```

### After (GraphQL-SSE Format)

SSE responses now use the proper graphql-transport-ws event stream format:

```
event: next
data: {"payload":{"data":{"check":"Hello"}}}
```

## Technical Details

### Event Types

The implementation emits the following event types as defined in the graphql-transport-ws specification:

- `next`: Sent when a new subscription result is available
- `complete`: Sent when the subscription stream has finished
- `error`: Sent when an error occurs during subscription execution

### Protocol Benefits

1. **Persistent Connection**: Unlike polling, SSE maintains a persistent HTTP connection
2. **Automatic Reconnection**: SSE clients can automatically reconnect on connection loss
3. **Efficient Streaming**: Data is streamed immediately as it becomes available
4. **Standards Compliant**: Follows the graphql-transport-ws specification for subscription transport

## Migration Guide

No migration is required for existing subscriptions. The new GraphQL-SSE format is automatically used when the client requests `text/event-stream` or `multipart/mixed` content types.

Existing subscription code will continue to work without modification.

## Requirements

- Strawberry GraphQL 0.313.0 or higher
- HTTP framework with SSE support (Starlette, FastAPI, etc.)
- Client that supports graphql-transport-ws (e.g., urql, Apollo Client)

## See Also

- [GraphQL Over HTTP Specification](https://graphql.github.io/graphql-over-http/)
- [graphql-transport-ws Protocol](https://github.com/enisdenjo/graphql-transport-ws)

--------------------------------------------------------------------------

# Future Work Recommendations

### 1. 🔒 Security Hardening (High Priority)

The recent CVEs (CVE-2026-35526, CVE-2026-35523) reveal a pattern of WebSocket security gaps. Recommendations:

- **Rate limiting per IP/client**: Add configurable rate limiting for subscription creation, not just per-connection limits. The current `max_subscriptions_per_connection=100` is good but doesn't prevent many short-lived connections.
- **Authentication/authorization audit**: Audit the SSE transport path (`_get_sse_stream`, `_is_sse_subscription`) to ensure it has equivalent auth checks to the WebSocket path. The SSE path currently doesn't go through `on_ws_connect` — consider adding an equivalent `on_sse_connect` hook.
- **Connection timeout configuration**: The heartbeat interval (5 seconds in `_stream_sse_with_heartbeat`) is hardcoded. Make it configurable and add a max connection duration.

### 2. 📡 SSE Protocol Completeness (Medium Priority)

The GraphQL-SSE implementation is new and has room for improvement:

- **`graphql-sse` protocol compliance**: The [`_is_sse_subscription`](strawberry/strawberry/http/base.py#L86-90) check is very basic — it just checks for `"text/event-stream" in accept`. Consider also supporting the `application/graphql-event-stream+json` content type used by some clients.
- **Connection introspection**: Add an SSE endpoint that supports the `connectionInit` / `connectionAck` handshake pattern from the graphql-transport-ws spec, so SSE clients can receive initial connection payload.
- **Graceful error streaming**: Currently errors in `_get_sse_stream` go through the generic `drain()` exception path. Add explicit `event: error` SSE events matching the graphql-transport-ws error format for better client-side error handling.
- **Last-Event-ID support**: For automatic reconnection, implement `Last-Event-ID` header support so clients can resume from where they disconnected.

### 3. 🧪 Test Coverage Gaps (Medium Priority)

Looking at the test file [`test_sse_subscription.py`](strawberry/tests/http/incremental/test_sse_subscription.py), there are 9 tests but some scenarios are untested:

- **Concurrent SSE connection limits**: Add tests for per-IP or global SSE connection limits (not just WebSocket).
- **SSE over all framework integrations**: Verify SSE works across FastAPI, Starlette, Django, Flask, Sanic, Quart, Litestar, and aiohttp. Currently tests may only cover a subset.
- **SSE + Federation**: Test SSE subscriptions with Apollo Federation schemas.
- **SSE reconnection behavior**: Test client disconnect mid-stream and verify server-side cleanup (no resource leaks).
- **Large payload streaming**: Test SSE with subscription results containing large nested objects.

### 4. 🛠️ Developer Experience (Medium Priority)

- **SSE debugging tools**: Add logging/telemetry for SSE connections similar to WebSocket debug logging. The `_get_sse_stream` and `_stream_sse_with_heartbeat` methods have no debug output.
- **Type-safe protocol handling**: The `protocol` field in `GraphQLRequestData` uses `Literal["http", "multipart-subscription", "graphql-sse"]`. Consider making this an enum for better type safety and extensibility.
- **Documentation for SSE-specific extensions**: Document how custom `strawberry.extensions` interact with SSE subscriptions (e.g., `ApolloTracingExtension` was recently fixed for invalid queries — does it work with SSE?).

### 5. 🏗️ Architecture & Performance (Long Term)

- **Unified subscription transport abstraction**: Currently SSE, multipart, and WebSocket subscriptions have separate code paths. Consider a unified `SubscriptionTransport` abstraction to reduce duplication and ensure feature parity.
- **Backpressure handling**: In `_stream_sse_with_heartbeat`, the queue has `maxsize=1`. If the client is slow, this could block. Consider configurable buffer sizes and backpressure strategies.
- **SSE connection pooling metrics**: Add metrics for active SSE connections, subscription duration, and event throughput. This is critical for production monitoring since SSE connections are long-lived.

### 6. ✊ ASGI Support

#### WebSocket Support (by the view, not HTTP client)

| Framework | WebSocket | Notes |
|-----------|-----------|-------|
| Django | ❌ NO | `AsyncGraphQLView` raises `NotImplementedError` for websocket methods |
| Flask | ❌ NO | `AsyncGraphQLView` raises `NotImplementedError` |
| Sanic | ❌ NO | `GraphQLView` raises `NotImplementedError` |
| Channels | ✅ YES | Has `GraphQLWsHandler` |
| FastAPI, Quart, Litestar, AioHttp, ASGI | ✅ YES | Full support |

#### SSE Support

| Framework | SSE Support | Notes |
|-----------|-------------|-------|
| Sync clients (Django sync, Flask sync, Chalice) | ❌ NO | Use `SyncBaseHTTPView` which never sets `protocol="graphql-sse"`. Adding SSE would require async streaming which sync views can't do. |
| Async clients (AsyncDjango, AsyncFlask, Sanic) | ⚠️ PARTIAL | Extend `AsyncBaseHTTPView` which has full SSE support, but their HTTP clients don't accept `max_subscriptions_per_connection`. |

#### Key Issues

1. **Sync clients**: `SyncBaseHTTPView.parse_http_body()` line 164-168 sets `protocol` to only `"http"` or `"multipart-subscription"`, never `"graphql-sse"`.

2. **Async clients**: `SanicHttpClient`, `AsyncDjangoHttpClient`, and `AsyncFlaskHttpClient` don't accept `max_subscriptions_per_connection` in their `__init__`, causing `TypeError` when testing SSE subscription limits.
