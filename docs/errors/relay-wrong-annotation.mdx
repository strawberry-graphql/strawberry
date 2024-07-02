---
title: Relay wrong annotation Error
---

# Relay wrong annotation error

## Description

This error is thrown when a field on a relay connection has a wrong type
annotation. For example, the following code will throw this error:

```python
from typing import List

import strawberry
from strawberry import relay


@strawberry.type
class MyType(relay.Node): ...


@strawberry.type
class Query:
    # The annotation is not a subclass of relay.Connection
    my_type_conn: List[MyType] = relay.connection()

    # Missing the Connection class annotation
    @relay.connection
    def my_type_conn_with_resolver(self) -> List[MyType]: ...

    # The connection class is not a subclass of relay.Connection
    @relay.connection(List[MyType])
    def my_type_conn_with_resolver2(self) -> List[MyType]: ...
```

## How to fix this error

You can fix this error by properly annotating your attribute or resolver with
`relay.Connection` type subclass.

For example:

```python
from typing import List

import strawberry
from strawberry import relay


@strawberry.type
class MyType(relay.Node): ...


def get_my_type_list() -> List[MyType]: ...


@strawberry.type
class Query:
    my_type_conn: relay.Connection[MyType] = relay.connection(
        resolver=get_my_type_list,
    )

    # Missing the Connection class annotation
    @relay.connection(relay.Connection[MyType])
    def my_type_conn_with_resolver(self) -> List[MyType]: ...

    # The connection class is not a subclass of relay.Connection
    @relay.connection(relay.Connection[MyType])
    def my_type_conn_with_resolver2(self) -> List[MyType]: ...
```
