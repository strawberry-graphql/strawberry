---
title: Unsupported Relay Node Error
---

# Unsupported Relay Node Error

## Description

This error is thrown when a `strawberry.pydantic.type` or
`strawberry.pydantic.interface` implements `relay.Node`, for example the
following code will throw this error:

```python
import pydantic
import strawberry
from strawberry import relay


@strawberry.pydantic.type
class Fruit(pydantic.BaseModel, relay.Node):
    id: relay.NodeID[int]
    name: str
```

This happens because `strawberry.pydantic` doesn't support `relay.Node` yet:
Pydantic types don't get the `id` field that `relay.Node` resolves from the
`relay.NodeID` field, and `relay.NodeID` hides the `id` field of the model, so
the type wouldn't implement the interface.

## How to fix this error

You can fix this error by using a regular `@strawberry.type` for the node, and
creating it from the model. `dict(model)` gives the values of the fields of the
model, keeping nested models as they are, so that they can be resolved with
their own `strawberry.pydantic` types:

```python
from collections.abc import Iterable

import pydantic
import strawberry
from strawberry import relay


class FruitModel(pydantic.BaseModel):
    id: int
    name: str


fruits = {1: FruitModel(id=1, name="Strawberry")}


@strawberry.type
class Fruit(relay.Node):
    id: relay.NodeID[int]
    name: str

    @classmethod
    def resolve_nodes(
        cls,
        *,
        info: strawberry.Info,
        node_ids: Iterable[str],
        required: bool = False,
    ):
        return [Fruit(**dict(fruits[int(node_id)])) for node_id in node_ids]


@strawberry.type
class Query:
    node: relay.Node = relay.node()

    @relay.connection(relay.ListConnection[Fruit])
    def fruits(self) -> list[Fruit]:
        return [Fruit(**dict(fruit)) for fruit in fruits.values()]


schema = strawberry.Schema(query=Query)
```

Pydantic types that don't implement `relay.Node` can still be the nodes of
connections, like `relay.ListConnection`:

```python
import pydantic
import strawberry
from strawberry import relay


@strawberry.pydantic.type
class Fruit(pydantic.BaseModel):
    name: str


@strawberry.type
class Query:
    @relay.connection(relay.ListConnection[Fruit])
    def fruits(self) -> list[Fruit]:
        return [Fruit(name="Strawberry")]


schema = strawberry.Schema(query=Query)
```
