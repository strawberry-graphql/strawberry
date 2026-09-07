---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! This release fixes avoidable overhead when
    checking resolver results for awaitability.
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release fixes avoidable overhead in
    awaitable detection while preserving support for synchronous results,
    coroutines, and custom awaitables.
---

This release fixes avoidable function-call overhead when checking resolver results
for awaitability.

Strawberry performs the existing graphql-core checks directly, preserving attribute
access order, side effects, and exception behavior. The existing fast path for
built-in scalar and container types is unchanged.
