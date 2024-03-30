---
title: Disable Validation
summary: Disable all query validation.
tags: performance,validation
---

# `DisableValidation`

This extensions disables all query validation. This can be useful to improve
performance in some specific cases, for example when dealing with internal APIs
where queries can be trusted.

<Warning>

Only do this if you know what you are doing! Disabling validation breaks the
safety of having typed schema. If you are trying to improve performance you
might want to consider using the [ValidationCache](./validation-cache) instead.

</Warning>

## Usage example:

```python
import strawberry
from strawberry.extensions import DisableValidation

schema = strawberry.Schema(
    Query,
    extensions=[
        DisableValidation(),
    ],
)
```

## API reference:

_No arguments_
