---
release type: minor
social_messages:
  x: >-
    {project_name} {version} is out! This release bounds the ParserCache and
    ValidationCache extensions by default, protecting servers from unbounded
    memory growth. 🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release changes the ParserCache and
    ValidationCache extensions to use a bounded LRU cache by default (128
    entries), so enabling them on a public endpoint no longer allows clients to
    grow server memory without limit by sending unique query texts. An unbounded
    cache is still available by explicitly passing maxsize=None.
---

This release fixes a potential unbounded memory growth in the `ParserCache` and
`ValidationCache` extensions.

Both extensions previously defaulted to `maxsize=None`, which creates an
unbounded `functools.lru_cache`. On a network-exposed endpoint with one of these
extensions enabled, a client sending many distinct query texts could grow the
server's memory without limit.

The default is now a bounded LRU cache of 128 entries, matching the
`functools.lru_cache` default. Existing behavior can be restored by explicitly
opting in to an unbounded cache:

```python
import strawberry
from strawberry.extensions import ParserCache, ValidationCache

schema = strawberry.Schema(
    Query,
    extensions=[
        ParserCache(maxsize=None),  # explicitly unbounded
        ValidationCache(maxsize=100),
    ],
)
```

Only use `maxsize=None` when the set of distinct query texts reaching the server
is trusted and bounded.
