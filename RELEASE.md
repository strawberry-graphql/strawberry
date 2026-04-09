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

No migration is required for existing subscriptions. The new GraphQL-SSE format is automatically used when the client requests `Accept: text/event-stream` over http/https

Existing subscription code will continue to work without modification.

## Requirements

- Strawberry GraphQL 0.313.0 or higher
- HTTP framework with EventSource/Streaming support (Starlette, FastAPI, etc.)
- Client that supports graphql-sse (e.g., urql, Apollo Client)

## See Also

- [GraphQL Over HTTP Specification](https://graphql.github.io/graphql-over-http/)
- [graphql-sse Protocol](https://github.com/enisdenjo/graphql-sse))

--------------------------------------------------------------------------

# Future Work Recommendations

### 1. 🔒 Security Hardening (High Priority)

**Completed in this release:**

- **Connection timeout configuration** ✅: Heartbeat interval is now configurable via `sse_heartbeat_interval: float = 5.0` attribute on `AsyncBaseHTTPView`

- **Authentication/authorization hook** ✅: Added `on_sse_connect` hook to `AsyncBaseHTTPView` (mirroring `on_ws_connect`). When `ConnectionRejectionError` is raised, the server returns a 403 error event. The hook supports returning `UNSET` (accept), a dict (accept with payload), or raising `ConnectionRejectionError` (reject).



### 2. 📡 SSE Protocol Completeness

**Completed in this release:**

- **`graphql-sse` protocol compliance** ✅: `_is_sse_subscription` now supports both `text/event-stream` and `application/graphql-event-stream+json` content types
- **Graceful error streaming** ✅: `_get_sse_stream` now catches exceptions and yields `event: error` before completing. The `_make_heartbeat_stream` helper emits error events when `emit_error_event=True`
- **SSE debugging/logging** ✅: Added `log.error("SSE stream error: %s", data)` when stream errors occur
- **Last-Event-ID support** ✅: SSE events now include `id:` fields for reconnection support. Server parses `Last-Event-ID` header and continues event numbering from that point.

**Remaining GRAPHQL-SSE protocol work:**

- Re-use single connection via `PUT` reservation and 
  - A header value X-GraphQL-Event-Stream-Token 
  - Or a search parameter token
  - **WARNING**: Adds complexity with zero upside for http/2+

### 3. 🧪 Test Coverage Gaps

**Completed in this release:**

- **Heartbeat comment parsing test** ✅: Added `test_streaming_sse_ignores_heartbeat_comments` to verify SSE comment lines (heartbeats) are correctly skipped
- **Error resolver assertions strengthened** ✅: `test_sse_subscription_with_error_in_resolver` now properly validates `data is None`, `errors` presence, error message, and path
- **Malformed JSON body test** ✅: Added `test_sse_subscription_with_malformed_json_body` to verify 400 response for invalid JSON
- **Large payload streaming test** ✅: Added `test_sse_subscription_with_large_payload` to verify large nested objects work
- **SSE data field compliance tests** ✅: Added `test_sse_complete_event_has_empty_data_field`, `test_sse_next_event_has_data_field`, and `test_sse_error_event_yields_next_event_with_errors` to verify SSE events include proper `data:` fields per the EventSource spec

- **SSE auth tests** ✅: Added `test_sse_connect_rejection_returns_forbidden_error_event`, `test_sse_connect_acceptance_proceeds_normally`, `test_sse_connect_with_custom_rejection_payload`, and `test_sse_connect_can_modify_context` to verify `on_sse_connect` hook works correctly

**Remaining test gaps:**

None - all test gaps are addressed.

**Completed test gaps:**
- **SSE + Federation** ✅: Added tests verifying SSE subscriptions work with Apollo Federation schemas
- **SSE reconnection with Last-Event-ID** ✅: Added tests for full reconnection flow with event ID tracking

### 4. 🛠️ Developer Experience (Medium Priority)

**Completed in this release:**

- **Type-safe protocol handling** ✅: `protocol` field in `GraphQLRequestData` now uses `GraphQLSubscriptionProtocol` enum instead of `Literal`

**Remaining DX work:**

None - all DX work is addressed.

**Completed DX work:**
- **SSE extensions documentation** ✅: Added section in `docs/general/sse-subscriptions.md` explaining how schema extensions work with SSE subscriptions

### 5. 🏗️ Architecture & Performance (Long Term)

**Completed in this release:**

- **Unified subscription transport abstraction** ✅: Extracted `_make_heartbeat_stream` as shared helper to reduce duplication between SSE and multipart heartbeat streams
- **Backpressure handling** ✅: Added configurable `sse_queue_buffer_size` attribute on `AsyncBaseHTTPView` and `queue_maxsize` parameter to `_make_heartbeat_stream` for configurable buffer sizes

**Remaining architecture work:**

- **SSE connection pooling metrics**: Add metrics for active SSE connections, subscription duration, and event throughput

### 6. ✊ ASGI Support

#### WebSocket Support (by the view, not HTTP client)

| Framework | WebSocket | Notes |
|-----------|-----------|-------|
| Django | ❌ NO | `AsyncGraphQLView` raises `NotImplementedError` for websocket methods |
| Flask | ❌ NO | `AsyncGraphQLView` raises `NotImplementedError` |
| Sanic | ❌ NO | `GraphQLView` raises `NotImplementedError` |
| Channels | ✅ YES | Has `GraphQLWsHandler` |
| FastAPI, Quart, Litestar, AioHTTP, ASGI | ✅ YES | Full support |

#### SSE Support

| Framework | SSE Support | Notes |
|-----------|-------------|-------|
| Sync clients (Django sync, Flask sync, Chalice) | ❌ NO | Use `SyncBaseHTTPView` which never sets `protocol="graphql-sse"`. Adding SSE would require async streaming which sync views can't do. |
| Async clients (AsyncDjango, AsyncFlask, Sanic) | ⚠️ PARTIAL | Extend `AsyncBaseHTTPView` which has full SSE support, but their HTTP clients don't accept `max_subscriptions_per_connection`. |

#### Key Issues

1. **Sync clients**: `SyncBaseHTTPView.parse_http_body()` line 164-168 sets `protocol` to only `"http"` or `"multipart-subscription"`, never `"graphql-sse"`.

2. **Async clients**: `SanicHttpClient`, `AsyncDjangoHttpClient`, and `AsyncFlaskHttpClient` don't accept `max_subscriptions_per_connection` in their `__init__`, causing `TypeError` when testing SSE subscription limits.
