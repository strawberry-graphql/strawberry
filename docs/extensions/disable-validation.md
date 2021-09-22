---
title: DisableValidation
summary: Disable all query validation.
tags: performance
---

# `DisableValidation`

This extensions disables all query validation.

**Note:** Only do this if you know what you are doing! If you are trying to
improve performance by disable validation you might want to consider using the
[ValidationCache](./validation-cache) instead.

## Usage example:

```python
import strawberry
from strawberry.extensions import DisableValidation

schema = strawberry.Schema(
    Query,
    extensions=[
        DisableValidation(),
    ]
)
```

## API reference:

*No arguments*
