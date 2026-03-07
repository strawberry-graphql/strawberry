Release type: patch

Fix sync execution crash with graphql-core 3.3 where `execute_sync()` would return a coroutine instead of an `ExecutionResult` — causing `RuntimeError: There is no current event loop` — because graphql-core 3.3's `is_async_iterable` default treats objects with `__aiter__` (like Django QuerySets) as async iterables. Now passes `is_async_iterable=lambda _x: False` during sync execution to prevent this.
