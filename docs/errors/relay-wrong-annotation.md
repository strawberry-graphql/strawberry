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
from strawberry import relay


@strawberry.type
class NonNodeSubclassType:
    ...


@strawberry.type
class Query:
    @relay.connection
    def some_connection(self) -> int:
        ...

    @relay.connection
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
from strawberry import relay


@strawberry.type
class NodeSubclassType(relay.Node):
    ...


@strawberry.type
class Query:
    @relay.connection
    def some_connection(self) -> List[NodeSubclassType]:
        ...

    @relay.connection
    def some_other_connection(self) -> Iterable[NodeSubclassType]:
        ...
```
