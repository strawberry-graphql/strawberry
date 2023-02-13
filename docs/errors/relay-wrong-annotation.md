---
title: Relay wrong annotation Error
---

# Relay wrong annotation error

## Description

This error is thrown when a field on a relay connection has a wrong
type annotation. For example, the following code will throw this error:

```python
from typing import List

import strawberry


@strawberry.type
class NonNodeSubclassType:
    ...


@strawberry.type
class Query:
    @strawberry.relay.connection
    def some_connection(self) -> int:
        ...

    @strawberry.relay.connection
    def some_other_connection(self) -> List[NonNodeSubclassType]:
        ...
```

This happens because when defining a custom resolver for the connection,
it expects the type annotation to be one of: `Iterable[<NodeType>]`,
`Iterator[<NodeType>]`, `AsyncIterable[<NodeType>]` or `AsyncIterator[<NodeType]`

## How to fix this error

You can fix this error by annotating the connection custom resolver with
one of the following possibilities:

- `Iterable[<NodeType>]`
- `Iterator[<NodeType>]`
- `AsyncIterable[<NodeType>]`
- `AsyncIterator[<NodeType]`

For example:

```python
from typing import Iterable, List

import strawberry


@strawberry.type
class NodeSubclassType(strawberry.relay.Node):
    ...


@strawberry.type
class Query:
    @strawberry.relay.connection
    def some_connection(self) -> List[NodeSubclassType]:
        ...

    @strawberry.relay.connection
    def some_other_connection(self) -> Iterable[NodeSubclassType]:
        ...
```
