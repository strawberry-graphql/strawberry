---
title: Pydantic support
experimental: true
---

# Pydantic support

Strawberry comes with support for
[Pydantic](https://pydantic-docs.helpmanual.io/). This allows for the creation
of Strawberry types from pydantic models without having to write code twice.

Here's a basic example of how this works, let's say we have a pydantic Model for
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

We can create a Strawberry type by using the
`strawberry.experimental.pydantic.type` decorator:

```python
import strawberry

from .models import User

@strawberry.experimental.pydantic.type(model=User, fields=[
    'id',
    'name',
    'friends'
])
class UserType:
    pass
```

The `strawberry.experimental.pydantic.type` decorator accepts a Pydantic model
and a list of fields that we want to expose on our GraphQL API.

> **Note** specifying the list of field is required to prevent accidentally
> exposing fields that weren't meant to be exposed on a API

## Input types

Input types are similar to types; we can create one by using the
`strawberry.experimental.pydantic.input` decorator:

```python
import strawberry

from .models import User

@strawberry.experimental.pydantic.input(model=User, fields=[
    'id',
    'name',
    'friends'
])
class UserInput:
    pass
```

## Interface types

Interface types are similar to normal types; we can create one by using the
`strawberry.experimental.pydantic.interface` decorator:

```python
import strawberry
from pydantic import BaseModel
from typing import List

# pydantic types
class User(BaseModel):
    id: int
    name: str

class NormalUser(User):
    friends: List[int] = []

class AdminUser(User):
    role: int

# strawberry types
@strawberry.experimental.pydantic.interface(model=User, fields=[
    'id',
    'name',
])
class UserType:
    pass

@strawberry.experimental.pydantic.type(model=NormalUser, fields=[
    'friends',
])
class NormalUserType(UserType):  # note the base class
    pass

@strawberry.experimental.pydantic.type(model=AdminUser, fields=[
    'role',
])
class AdminUserType(UserType):
    pass
```

## Error Types

In addition to object types and input types, Strawberry allows you to create
"error types". You can use these error types to have a typed representation of
Pydantic errors in GraphQL. Let's see an example:

```python+schema
import pydantic
import strawberry

class User(BaseModel):
    id: int
    name: pydantic.constr(min_length=2)
    signup_ts: Optional[datetime] = None
    friends: List[int] = []

@strawberry.experimental.pydantic.error_type(model=User, fields=[
    'id',
    'name',
    'friends'
])
class UserError:
    pass

---

type UserError {
  id: [String!]
  name: [String!]
  friends: [[String!]]
}
```

where each field will hold a list of error messages

### Extending types

You can use the usual Strawberry syntax to add additional new fields to the
GraphQL type that aren't defined in the pydantic model

```python+schema
import strawberry
import pydantic

from .models import User

class User(BaseModel):
    id: int
    name: str

@strawberry.experimental.pydantic.type(model=User, fields=[
    'id',
    'name',
])
class User:
    age: int

---

type User {
    id: Int!
    name: String!
    age: Int!
}
```

### Converting types

The generated types won't run any pydantic validation. This is to prevent
confusion when extending types and also to be able to run validation exactly
where it is needed.

To convert a Pydantic instance to a Strawberry instance you can use
`from_pydantic` on the Strawberry type:

```python
import strawberry
from typing import List, Optional
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str


@strawberry.experimental.pydantic.type(model=User, fields=[
    'id',
    'name',
])
class UserType:
    pass

instance = User(id='123', name='Jake')

data = UserType.from_pydantic(instance)
```

If your Strawberry type includes additional fields that aren't defined in the
pydantic model, you will need to use the `extra` parameter of `from_pydantic` to
specify the values to assign to them.

```python
import strawberry
from typing import List, Optional
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str


@strawberry.experimental.pydantic.type(model=User, fields=[
    'id',
    'name',
])
class UserType:
    age: int

instance = User(id='123', name='Jake')

data = UserType.from_pydantic(instance, extra={'age': 10})
```

The data dictionary structure follows the structure of your data -- if you have
a list of `User`, you should send an `extra` that is the list of `User` with the
missing data (in this case, `age`).

You don't need to send all fields; data from the model is used first and then
the `extra` parameter is used to fill in any additional missing data.

To convert a Strawberry instance to a pydantic instance and trigger validation,
you can use `to_pydantic` on the Strawberry instance:

```python
import strawberry
from typing import List, Optional
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str


@strawberry.experimental.pydantic.input(model=User, fields=[
    'id',
    'name',
])
class UserInput:
    pass

input_data = UserInput(id='abc', name='Jake')

# this will run pydantic's validation
instance = input_data.to_pydantic()
```
