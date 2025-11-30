---
title: Multiple Strawberry Fields Error
---

# Multiple Strawberry Fields Error

## Description

This error is raised when using multiple `strawberry.field()` annotations inside
an `Annotated` type. For example, the following code will raise this error:

```python
from typing import Annotated

import strawberry


@strawberry.type
class Query:
    name: Annotated[
        str,
        strawberry.field(description="First"),
        strawberry.field(description="Second"),
    ]


schema = strawberry.Schema(query=Query)
```

This happens because Strawberry only allows one `strawberry.field()` per field
when using the `Annotated` syntax. Having multiple would create ambiguity about
which field configuration to use.

## How to fix this error

You can fix this error by using only one `strawberry.field()` in your
`Annotated` type annotation. Combine all the options you need into a single
`strawberry.field()` call:

```python
from typing import Annotated

import strawberry


@strawberry.type
class Query:
    name: Annotated[
        str,
        strawberry.field(
            description="The name",
            deprecation_reason="Use fullName instead",
        ),
    ]


schema = strawberry.Schema(query=Query)
```
