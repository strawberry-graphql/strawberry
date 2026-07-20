---
release type: minor
social_messages:
  x: >-
    {project_name} {version} is out! Streaming transports now apply extensions
    before sending GraphQL results, so MaskErrors protects WebSocket, SSE, and
    multipart responses. 🍓
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release adds an on_stream_result hook
    for extension authors who need to inspect or mutate GraphQL results before
    WebSocket, SSE, or multipart transports send them. Strawberry's MaskErrors
    extension now uses it to mask streamed query, mutation, and subscription
    errors consistently.
---

This release adds an `on_stream_result` hook to `SchemaExtension` for extension
authors who need to inspect or mutate GraphQL results before they reach a
streaming transport.

The hook wraps each Strawberry `ExecutionResult` yielded by `Schema.stream`,
including subscription events and queries or mutations sent over WebSockets,
SSE, or multipart responses. Raw incremental-delivery patch frames are excluded.

Strawberry's built-in `MaskErrors` extension now uses the hook so streamed query,
mutation, subscription, and pre-execution errors are masked before being sent to
clients.
