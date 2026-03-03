Release type: patch

Fix `ApolloTracingExtension` crashing with `AttributeError` when executing invalid queries (e.g., `{ node() }`). All timing attributes are now initialized in `__init__` and lifecycle hooks use `try/finally` to ensure proper cleanup.
