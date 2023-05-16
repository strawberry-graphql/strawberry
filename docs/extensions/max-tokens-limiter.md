---
title: MaxTokensLimiter
summary: Add a validator to limit the maximum number of tokens in a GraphQL document.
tags: security
---

# `MaxTokensLimiter`

This extension adds a validator to limit the maximum number of tokens in a GraphQL document.

## Usage example:

```python
import strawberry
from strawberry.extensions import MaxTokensLimiter

schema = strawberry.Schema(
    Query,
    extensions=[
        MaxTokensLimiter(max_token_count=1000),
    ],
)
```

## API reference:

```python
class MaxTokensLimiter(max_token_count):
    ...
```

#### `max_token_count: int`

The maximum allowed number of tokens in a GraphQL document.

The following things are counted as tokens:

- various brackets: "{", "}", "(", ")"
- colon :
- words

Not counted:

- quotes
