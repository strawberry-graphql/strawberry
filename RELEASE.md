---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! This release fixes the legacy graphql-ws
    handler so completed subscriptions no longer count towards
    max_subscriptions_per_connection. 🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release fixes the legacy graphql-ws
    handler so subscriptions that complete on their own release their slot and
    no longer count towards max_subscriptions_per_connection.
---

This release fixes the legacy `graphql-ws` protocol handler so that
subscriptions which complete on their own (or fail before execution) release
their slot on the connection.

Previously, completed operations were kept in the handler's bookkeeping until
the client sent a `stop` message for them, reused their operation id, or
disconnected. On connections with `max_subscriptions_per_connection`
configured, a client using distinct operation ids could therefore hit
`Subscription limit reached` even though none of its earlier subscriptions
were still active. The `graphql-transport-ws` handler was not affected.

Sending a `stop` message for an operation that has already completed is now a
no-op instead of an error.
