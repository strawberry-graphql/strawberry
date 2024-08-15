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

schema = strawberry.Schema(
    Query,
    extensions=[
        ValidationCache(),
    ],
)
```

## API reference:

```python
class ValidationCache(maxsize=None): ...
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
from strawberry.extensions import ValidationCache

schema = strawberry.Schema(
    Query,
    extensions=[
        ValidationCache(maxsize=100),
    ],
)
```

</details>
