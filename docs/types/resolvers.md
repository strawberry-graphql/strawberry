---
title: Resolvers
---

# Resolvers

When defining a GraphQL schema, you usually start with the definition of the
structure of the API, for example, let's take a look at this schema:

```python+schema
from typing import Optional

import strawberry

@strawberry.type
class User:
    name: str


@strawberry.type
class Query:
    last_user: Optional[User]
---
type User {
    name: String!
}

type Query {
    lastUser: User
}
```

we have defined a `User` type and a `Query` type. To define how the data is
returned from our server, we use `resolvers` and we attached them to fields.

## Let's define a resolver

Let's create a resolver and attach it to the `lastUser` field. A resolver is a
python function that returns data. In Strawberry there are two ways of defining
resolvers, the first one is to create a function and then pass it to the field
definition, like this:

```python
def get_last_user() -> Optional[User]:
    return User(name="Marco")

@strawberry.type
class Query:
    last_user: Optional[User] = strawberry.field(resolver=get_last_user)
```

When executing this following query Strawberry knows that it needs to call the
`get_last_user` function to fetch the data for the `lastUser` field:

```graphql+response
{
  lastUser {
    name
  }
}
---
{
  "data": {
    "lastUser": {
      "name": "Marco"
    }
  }
}
```

## Defining resolvers as methods

The other way to define a resolver is to use `strawberry.field` as a decorator,
like here:

```python

@strawberry.type
class Query:
    @strawberry.field
    def last_user(self) -> Optional[User]:
        return User(name="Marco")
```

this is useful when you want to colocate resolvers and types or when you have
very small resolvers.

> _NOTE:_ the _self_ argument is a bit special here, when executing a GraphQL
> query, in case of resolvers defined with a decorator, the _self_ argument
> corresponds to the _root_ value that field, in this example the _root_ value
> is the value `Query` type, which is usually `None`, you can change the _root_
> value when calling the `execute` method on a `Schema`. More on root values
> below

## Defining arguments

Fields can also have arguments; in Strawberry the arguments for a field are
defined on the resolver, as you would normally do in a python function. Let's
define a field on a Query that returns a user by ID:

```python+schema
from typing import Optional

import strawberry


@strawberry.type
class User:
    name: str


@strawberry.type
class Query:
    @strawberry.field
    def user(self, id: strawberry.ID) -> Optional[User]:
        return User(name="Marco")
---
type User {
    name: String!
}

type Query {
    user(id: ID!): User
}
```

## Accessing parent's data

It is quite common to want to be able to access the data from the parent in a
resolver, for example let's say that we want to defined a `fullName` field on
our user. We can defined a new field with a resolver that combines the first
name and last name:

```python+schema
import strawberry


@strawberry.type
class User:
    first_name: str
    last_name: str

    @strawberry.field
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
---
type User {
    firstName: String!
    lastName: String!
    fullName: String!
}
```

In the case of a decorated resolver you can use the _self_ parameter as you
would do in a normal python class[^1].

For resolvers defined as normal python functions you can use the special `root`
parameter, when defined, Strawberry will pass to it the value of the parent:

```python
import strawberry

def full_name(root: User) -> str:
    return f"{root.first_name} {root.last_name}"

@strawberry.type
class User:
    first_name: str
    last_name: str
    full_name: str = strawberry.field(resolver=full_name)
```

## Accessing execution information

Sometimes it is useful to access the information for the current execution
context, to do so you can provide the `info` parameter to resolvers, like this:

```python
import strawberry
from strawberry.types import info

def full_name(root: User, info: Info) -> str:
    return f"{root.first_name} {root.last_name} {info.field_name}"

@strawberry.type
class User:
    first_name: str
    last_name: str
    full_name: str = strawberry.field(resolver=full_name)
```

### API

`Info[ContextType, RootValueType]`

| Parameter name  | Type                       | Description                                                           |
| --------------- | -------------------------- | --------------------------------------------------------------------- |
| field_name      | `str`                      | The name of the current field                                         |
| context         | `ContextType`              | The value of the context                                              |
| root_value      | `RootValueType`            | The value for the root type                                           |
| variable_values | `Optional[Dict[str, Any]]` | The variables for this operation                                      |
| operation       | `OperationDefinitionNode`  | The ast for the current operation (public API might change in future) |
| path            | `Path`                     | The path for the current field                                        |

[^1]:
    see
    [this discussion](https://github.com/strawberry-graphql/strawberry/discussions/515)
    for more context around the self parameter.
