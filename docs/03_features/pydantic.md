---
title: Pydantic Support
path: /docs/feature/pydantic
---

# Pydantic support

Strawberry comes with support for
[Pydantic](https://pydantic-docs.helpmanual.io/). This allows to create
Strawberry types from Pydantic models without having to write code twice.

Here's a basic example of how this works, let's say we have a Pydantic Model for
a user, like this:

```python
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str
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

> **Note** specifying the list of field is required to prevent accidentally
> exposing fields that weren't meant to be exposed on a API

## Input types

Input types are similar to types, we can create one by using the
`strawberry.pydantic.input` decorator:

```python
import strawberry

from .models import User

@strawberry.pydantic.input(model=User, fields=[
    'id',
    'name',
    'friends'
])
class UserType:
    pass
```

## Error Types

In addition to object types and input types strawberry allows you to create
"error types", you can use these error types to have a typed representation of
Pydantic errors in GraphQL, let's see an example:

```python
import pydantic
import strawberry

class User(BaseModel):
    id: int
    name: pydantic.constr(min_length=2)
    signup_ts: Optional[datetime] = None
    friends: List[int] = []

@strawberry.pydantic.input(model=User, fields=[
    'id',
    'name',
    'friends'
])
class UserType:
    pass
```

### Converting types

The generated types won't run any pydantic validation, this is to prevent
confusion when extending types and also to be able to run validation exactly
where it is needed.

To convert a Pydantic instance to a strawberry instance you can use
`from_pydantic` on the strawberry type:

```python
import strawberry
from typing import List, Optional
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str


@strawberry.pydantic.type(model=User, fields=[
    'id',
    'name',
])
class UserType:
    pass

instance = User(id='123', name='Jake')

data = UserType.from_pydantic(instance)
```

To convert a strawberry instance to a pydantic instance and trigger validation,
you can use `to_pydantic` on the strawberry instance:

```python
import strawberry
from typing import List, Optional
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str


@strawberry.pydantic.input(model=User, fields=[
    'id',
    'name',
])
class UserInput:
    pass

input_data = UserInput(id='abc', name='Jake')

# this will run pydantic's validation

instance = input_data.to_pydantic()
```

Finally, you can also convert validation errors to a strawberry error type:

```python
import strawberry
from typing import List, Optional
from pydantic import BaseModel, ValidationError


class User(BaseModel):
    id: int
    name: str

@strawberry.pydantic.input(model=User, fields=[
    'id',
    'name',
])
class UserInput:
    pass

@strawberry.pydantic.error_type(model=User)
class UserInputError:
    pass

input_data = UserInput(id='abc', name='Jake')

# this will run pydantic's validation

try:
    instance = input_data.to_pydantic()
except ValidationError as e:
    error_data = UserInputError.from_error(e)
```

## Extending a type

...
