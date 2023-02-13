---
title: Relay wrong annotation Error
---

# Relay wrong annotation error

## Description

This error is thrown when a field on a relay connection was defined with
a `node_converter` that has the wrong type type annotation. For example,
the following code will throw this error:

```python
from typing import Iterable

import strawberry


@strawberry.type
class NonNodeSubclassType:
    ...


def node_converter(node_id: str) -> NonNodeSubclassType:
    ...


@strawberry.type
class Query:
    @strawberry.relay.connection(NonNodeSubclassType)
    def some_connection(self) -> Iterable[str]:
        ...
```

This happens because when defining a `node_converter`, it is expected
to be a function that receives the iterable element as its single argument,
and should return the correct strawberry `Node` implemented type.

## How to fix this error

You can fix this error by annotating the `node_converter` function to
return the correct strawberry `Node` implemented type.

For example:

```python
from typing import Iterable

import strawberry


@strawberry.type
class NodeSubclassType(strawberry.relay.Node):
    ...


def node_converter(node_id: str) -> NodeSubclassType:
    ...


@strawberry.type
class Query:
    @strawberry.relay.connection(node_converter=node_converter)
    def some_connection(self) -> Iterable[str]:
        ...
```
