---
title: Invalid Strawberry Field Annotation Error
---

# Invalid Strawberry Field Annotation Error

## Description

This error is raised when `strawberry.field()` is nested inside another type in
a class-field annotation. For example, this attempts to configure a list item,
which is not a GraphQL field:

```python
from typing import Annotated

import strawberry


@strawberry.type
class Query:
    names: list[Annotated[str, strawberry.field(description="A name")]]
```

Strawberry only uses `strawberry.field()` metadata from the outermost
`Annotated` type because that node represents the class field.

## How to fix this error

Move `strawberry.field()` to the outermost `Annotated` metadata for the field:

```python
from typing import Annotated

import strawberry


@strawberry.type
class Query:
    names: Annotated[list[str], strawberry.field(description="The names")]
```
