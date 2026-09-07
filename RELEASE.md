---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! A small optimization reduces overhead when
    running your GraphQL queries, with no code changes needed. 🍓
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. Strawberry now does a little less work when
    handling GraphQL resolver results. Your existing synchronous and asynchronous
    resolvers continue to work as before, with no code changes needed. 🍓
---

This release fixes unnecessary overhead when handling resolver results.

Strawberry now does a little less work to check whether a result needs to be
awaited. This small optimization works automatically with your existing
synchronous and asynchronous resolvers, with no code changes needed.
