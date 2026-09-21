---
title: Validation Cache
summary: Add in memory caching to the validation step of query execution.
tags: performance,caching,validation
---

# `ValidationCache`

This extension adds LRU caching to the validation step of query execution to
improve performance by caching the validation errors in memory.

## Usage example:

```python
import strawberry
from strawberry.extensions import ValidationCache


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello, world!"


schema = strawberry.Schema(
    Query,
    extensions=[
        ValidationCache(),
    ],
)
```

## API reference:

```python
class ValidationCache(maxsize=128): ...
```

#### `maxsize: Optional[int] = 128`

Set the maxsize of the cache. By default the cache is bounded to 128 entries,
with the least recently used entries evicted first. Pass an explicit
`maxsize=None` to let the cache grow without bound; only do this when the set of
distinct query texts reaching the server is trusted and bounded, as an unbounded
cache lets clients grow the server's memory indefinitely by sending unique query
texts.

More info: https://docs.python.org/3/library/functools.html#functools.lru_cache

## More examples:

<details>
  <summary>Using maxsize</summary>

```python
import strawberry
from strawberry.extensions import ValidationCache


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Hello, world!"


schema = strawberry.Schema(
    Query,
    extensions=[
        ValidationCache(maxsize=100),
    ],
)
```

</details>
