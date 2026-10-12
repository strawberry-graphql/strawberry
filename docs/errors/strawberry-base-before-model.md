---
title: Strawberry Base Before Model Error
---

# Strawberry Base Before Model Error

## Description

This error is thrown when a `strawberry.pydantic` type, input or interface
extends a regular Strawberry type, input or interface before its Pydantic model,
for example the following code will throw this error:

```python
import pydantic
import strawberry


@strawberry.interface
class Node:
    id: strawberry.ID


@strawberry.pydantic.type
class Product(Node, pydantic.BaseModel):
    name: str
```

Regular Strawberry types are dataclasses, so `Node` has its own `__init__`. As
`Node` comes before `pydantic.BaseModel` in `Product`'s bases, its `__init__`
would replace Pydantic's, and creating a `Product` would fail.

## How to fix this error

You can fix this error by listing the Pydantic model first:

```python
import pydantic
import strawberry


@strawberry.interface
class Node:
    id: strawberry.ID


@strawberry.pydantic.type
class Product(pydantic.BaseModel, Node):
    name: str
```
