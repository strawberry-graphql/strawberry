---
title: Pydantic Support
path: /docs/feature/pydantic
---

# Pydantic support

Strawberry comes with support for
[Pydantic](https://pydantic-docs.helpmanual.io/). This allows to create
Strawberry types from Pydantic models, while retaining the validation features
for Pydantic.

Here's a basic example of how this works, let's say we have a Pydantic Model for
a user, that looks like this:

```python
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name = 'John Doe'
    signup_ts: Optional[datetime] = None
    friends: List[int] = []
```

We can create a Strawberry type by using the `strawberry.pydantic.type`
decorator:

```python
import strawberry

from .models import User

@strawberry.pydantic.type(model=User, fields=[
    'id',
    'name',
    'friends'
])
class UserType:
    pass
```

The `strawberry.pydantic.type` decorator accepts a Pydantic model and a list of
fields that we want to expose on our GraphQL API.

> Note that the constructor method would still be the same as the Pydantic
> model, so even if some fields are not exposed they still need to be passed
> when constructing the Pydantic model (if required)

## Extending a type

...

## Input types

Input types are similar to types, we can create one by using the
`strawberry.pydantic.input` decorator:

```python
import strawberry

from .models import User

# TODO: do we need to specify fields here?

@strawberry.pydantic.input(model=User, fields=[
    'id',
    'name',
    'friends'
])
class UserType:
    pass
```

## Error Types

...
