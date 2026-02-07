Release type: patch

This release fixes a bug where the async `execute` method was creating
new extension instances on every request (via `get_extensions()`),
instead of reusing cached instances like the sync `execute_sync` method
already did. This caused extensions that accumulate state across the
execution lifecycle (such as `ApolloTracingExtension`) to lose their
state between requests when using async execution.
