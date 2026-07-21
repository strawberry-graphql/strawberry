---
release type: minor
social_messages:
  x: >-
    {project_name} {version} is out! Streaming transports now apply extensions
    before sending every GraphQL result, including supported incremental
    patches, so MaskErrors protects WebSocket, SSE, and multipart responses. 🍓
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release adds an on_stream_result hook
    for extension authors who need to inspect or mutate GraphQL results before
    WebSocket, SSE, or multipart transports send them. Strawberry's MaskErrors
    extension now uses it to mask streamed query, mutation, subscription, and
    incremental-delivery errors consistently.
---

This release adds an `on_stream_result` hook to `SchemaExtension` for extension
authors who need to inspect or mutate GraphQL results before they reach a
streaming transport.

The hook wraps subscription events and queries or mutations sent over WebSockets,
SSE, or multipart responses. On transports that support experimental incremental
execution, it also wraps each incremental-delivery frame.

Strawberry's built-in `MaskErrors` extension now uses the hook so streamed query,
mutation, subscription, incremental-delivery, and pre-execution errors are masked
before being sent to clients.
