---
title: Relay wrong resolver annotation Error
---

# Relay wrong resolver annotation error

## Description

This error is thrown when a field on a relay connection was defined with a
resolver that returns something that is not compatible with pagination.

For example, the following code would throw this error:

```python
from typing import Any

import strawberry
from strawberry import relay


@strawberry.type
class MyType(relay.Node): ...


@strawberry.type
class Query:
    @relay.connection(relay.Connection[MyType])
    def some_connection_returning_mytype(self) -> MyType: ...

    @relay.connection(relay.Connection[MyType])
    def some_connection_returning_any(self) -> Any: ...
```

This happens because the connection resolver needs to return something that can
be paginated, usually an iterable/generator of the connection type itself.

## How to fix this error

You can fix this error by annotating the resolver with one of the following
supported types:

- `List[<NodeType>]`
- `Iterator[<NodeType>]`
- `Iterable[<NodeType>]`
- `AsyncIterator[<NodeType>]`
- `AsyncIterable[<NodeType>]`
- `Generator[<NodeType>, Any, Any]`
- `AsyncGenerator[<NodeType>, Any]`

For example:

```python
from typing import Any

import strawberry
from strawberry import relay


@strawberry.type
class MyType(relay.Node): ...


@strawberry.type
class Query:
    @relay.connection(relay.Connection[MyType])
    def some_connection(self) -> Iterable[MyType]: ...
```

<Note>
  Note that if you are returning a type different than the connection type, you
  will need to subclass the connection type and override its `resolve_node`
  method to convert it to the correct type, as explained in the [relay
  guide](../guides/relay).
</Note>
