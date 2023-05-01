---
title: Unresolved Field Type Error
---

# Unresolved Field Type Error

## Description

This error is thrown when Strawberry is unable to resolve a field type. This
happens when the type of a field is not accessible in the current scope. For
example the following code will throw this error:

```python
import strawberry


@strawberry.type
class Query:
    user: "User"


schema = strawberry.Schema(query=Query)
```

<Note>

Note that we are using the forward reference syntax to define the type of the
field. This is because the `User` type is not yet defined when the `Query` type
is defined.

This would also happen when using `from __future__ import annotations`.

</Note>

To fix this error you need to import the type that you are using in the field,
for example:

```python
import strawberry
from .user import User


@strawberry.type
class Query:
    user: "User"


schema = strawberry.Schema(query=Query)
```

Unfortunately, this won't work in cases where there's a circular dependency
between types. In this case, you can use `strawberry.LazyType`.

<!-- TODO: document lazy type -->
