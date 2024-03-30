---
title: Parser Cache
summary: Add in memory caching to the parsing step of query execution.
tags: performance,caching,parsing
---

# `ParserCache`

This extension adds LRU caching to the parsing step of query execution to
improve performance by caching the parsed result in memory.

## Usage example:

```python
import strawberry
from strawberry.extensions import ParserCache

schema = strawberry.Schema(
    Query,
    extensions=[
        ParserCache(),
    ],
)
```

## API reference:

```python
class ParserCache(maxsize=None): ...
```

#### `maxsize: Optional[int] = None`

Set the maxsize of the cache. If `maxsize` is set to `None` then the cache will
grow without bound.

More info: https://docs.python.org/3/library/functools.html#functools.lru_cache

## More examples:

<details>
  <summary>Using maxsize</summary>

```python
import strawberry
from strawberry.extensions import ParserCache

schema = strawberry.Schema(
    Query,
    extensions=[
        ParserCache(maxsize=100),
    ],
)
```

</details>
