---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! This release adds CodSpeed benchmarks for
    awaitable detection and GraphQL execution to track future performance changes.
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release adds CodSpeed benchmarks for
    awaitable detection and synchronous and asynchronous GraphQL execution,
    providing a baseline for future performance work.
---

This release adds CodSpeed benchmarks for awaitable detection and GraphQL execution.

The benchmarks cover scalar and object results, native and generator coroutines,
custom awaitables, and small and large object-list queries. They establish a
baseline for measuring future optimizations without changing runtime behavior.
