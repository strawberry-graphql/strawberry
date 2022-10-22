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

## `CacheControl` directive

### API Reference:

```python
class CacheControl(
    max_age: Optional[int]
    scope: Optional[CacheControlScope]
    inheredit_max_age: Optional[bool]
)
```

#### `max_age: Optional[int]`

The maximum amount of time the field's cached value is valid, in seconds. The default value is 0, but you can set a different default for the schema in the `ApolloCacheControl` extension.

#### `scope: Optional[CacheControlScope]`

If `PRIVATE`, the field's value is specific to a single user. The default value is `PUBLIC`.

#### `inheredit_max_age: Optional[bool]`

If true, this field inherits the `max_age` of its parent field instead of using the default `max_age`. Do not provide `max_age` if you provide this argument.
