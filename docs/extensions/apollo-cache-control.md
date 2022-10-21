---
title: ApolloCacheControl
summary: Server side caching on a per-field basis
tags: apollo, performance, caching
---

# `ApolloCacheControl`

This extension allows you to define Apollo's server-side caching for each field in your schema.

## Usage example:

```python
import strawberry
from strawberry.apollo.schema_directives import CacheControl, CacheControlScope
from strawberry.extensions import ApolloCacheControl


@strawberry.type
class Book:
    title: str
    cachedtitle: str = strawberry.field(directives=[CacheControl(max_age=30)])

@strawberry.type
class Query:
    @strawberry.field(directives=[CacheControl(max_age=60)])
    def cached_book(
        self,
    ) -> Book:
        return Book(name="The Great Gatsby")

schema = strawberry.Schema(
    query=Query,
    extensions=[
        ApolloCacheControl(calculate_http_headers=False, default_max_age=10)
    ],
)
```

## API reference:

```python
class ApolloCacheControl(default_max_age=0, calculate_http_headers=True)`
```

### `default_max_age: Optional[int] = 0`

You can set a default `max_age` that's applied to fields that otherwise receive the default `max_age` of 0.

### `calculate_http_headers: Optional[bool] = True`

Adds `Cache-Control` headers to the response with the calculated `max_age` and `scope`
