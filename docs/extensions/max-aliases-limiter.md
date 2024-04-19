---
title: Max Aliases Limiter
summary:
  Add a validator to limit the maximum number of aliases in a GraphQL document.
tags: security
---

# `MaxAliasesLimiter`

This extension adds a validator to limit the maximum number of aliases in a
GraphQL document.

## Usage example:

```python
import strawberry
from strawberry.extensions import MaxAliasesLimiter

schema = strawberry.Schema(
    Query,
    extensions=[
        MaxAliasesLimiter(max_alias_count=15),
    ],
)
```

## API reference:

```python
class MaxAliasesLimiter(max_alias_count): ...
```

#### `max_alias_count: int`

The maximum allowed number of aliases in a GraphQL document.
