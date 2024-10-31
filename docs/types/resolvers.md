---
title: Resolvers
---

# Resolvers

When defining a GraphQL schema, you usually start with the definition of the
schema for your API, for example, let's take a look at this schema:

<CodeGrid>

```python
import strawberry


@strawberry.type
class User:
    name: str


@strawberry.type
class Query:
    last_user: User
```

```graphql
type User {
  name: String!
}

type Query {
  lastUser: User!
}
```

</CodeGrid>

We have defined a `User` type and a `Query` type. Next, to define how the data
is returned from our server, we will attach resolvers to our fields.

## Let's define a resolver

Let's create a resolver and attach it to the `lastUser` field. A resolver is a
Python function that returns data. In Strawberry there are two ways of defining
resolvers; the first is to pass a function to the field definition, like this:

```python
def get_last_user() -> User:
    return User(name="Marco")


@strawberry.type
class Query:
    last_user: User = strawberry.field(resolver=get_last_user)
```

Now when Strawberry executes the following query, it will call the
`get_last_user` function to fetch the data for the `lastUser` field:

<CodeGrid>

```graphql
{
  lastUser {
    name
  }
}
```

```json
{
  "data": {
    "lastUser": {
      "name": "Marco"
    }
  }
}
```

</CodeGrid>

## Defining resolvers as methods

The other way to define a resolver is to use `strawberry.field` as a decorator,
like here:

```python
@strawberry.type
class Query:
    @strawberry.field
    def last_user(self) -> User:
        return User(name="Marco")
```

This is useful when you want to co-locate resolvers and types or when you have
very small resolvers.

<Note>

If you're curious how the `self` parameter works in the resolver, you can read
more about it in the
[accessing parent data guide](../guides/accessing-parent-data.md).

</Note>

## Defining arguments

Fields can also have arguments; in Strawberry the arguments for a field are
defined on the resolver, as you would normally do in a Python function. Let's
define a field on a Query that returns a user by ID:

<CodeGrid>

```python
import strawberry


@strawberry.type
class User:
    name: str


@strawberry.type
class Query:
    @strawberry.field
    def user(self, id: strawberry.ID) -> User:
        # here you'd use the `id` to get the user from the database
        return User(name="Marco")
```

```graphql
type User {
  name: String!
}

type Query {
  user(id: ID!): User!
}
```

</CodeGrid>

### Optional arguments

Optional or nullable arguments can be expressed using `Optional`. If you need to
differentiate between `null` (maps to `None` in Python) and no arguments being
passed, you can use `UNSET`:

<CodeGrid>

```python
from typing import Optional
import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def hello(self, name: Optional[str] = None) -> str:
        if name is None:
            return "Hello world!"
        return f"Hello {name}!"

    @strawberry.field
    def greet(self, name: Optional[str] = strawberry.UNSET) -> str:
        if name is strawberry.UNSET:
            return "Name was not set!"
        if name is None:
            return "Name was null!"
        return f"Hello {name}!"
```

```graphql
type Query {
  hello(name: String = null): String!
  greet(name: String): String!
}
```

</CodeGrid>

Like this you will get the following responses:

<CodeGrid>

```graphql
{
  unset: greet
  null: greet(name: null)
  name: greet(name: "Dominique")
}
```

```json
{
  "data": {
    "unset": "Name was not set!",
    "null": "Name was null!",
    "name": "Hello Dominique!"
  }
}
```

</CodeGrid>

### Annotated Arguments

Additional metadata can be added to arguments, for example a custom name or
deprecation reason, using `strawberry.argument` with
[typing.Annotated](https://docs.python.org/3/library/typing.html#typing.Annotated):

```python
from typing import Optional, Annotated
import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def greet(
        self,
        name: Optional[str] = strawberry.UNSET,
        is_morning: Annotated[
            Optional[bool],
            strawberry.argument(
                name="morning",
                deprecation_reason="The field now automatically detects if it's morning or not",
            ),
        ] = None,
    ) -> str: ...
```

## Accessing execution information

Sometimes it is useful to access the information for the current execution
context. Strawberry allows to declare a parameter of type `Info` that will be
automatically passed to the resolver. This parameter contains the information
for the current execution context.

```python
import strawberry
from strawberry.types import Info


def full_name(root: "User", info: strawberry.Info) -> str:
    return f"{root.first_name} {root.last_name} {info.field_name}"


@strawberry.type
class User:
    first_name: str
    last_name: str
    full_name: str = strawberry.field(resolver=full_name)
```

<Tip>

You don't have to call this parameter `info`, its name can be anything.
Strawberry uses the type to pass the correct value to the resolver.

</Tip>

### API

Info objects contain information for the current execution context:

`class Info(Generic[ContextType, RootValueType])`

| Parameter name  | Type                      | Description                                                           |
| --------------- | ------------------------- | --------------------------------------------------------------------- |
| field_name      | `str`                     | The name of the current field (generally camel-cased)                 |
| python_name     | `str`                     | The 'Python name' of the field (generally snake-cased)                |
| context         | `ContextType`             | The value of the context                                              |
| root_value      | `RootValueType`           | The value for the root type                                           |
| variable_values | `Dict[str, Any]`          | The variables for this operation                                      |
| operation       | `OperationDefinitionNode` | The ast for the current operation (public API might change in future) |
| path            | `Path`                    | The path for the current field                                        |
| selected_fields | `List[SelectedField]`     | Additional information related to the current field                   |
| schema          | `Schema`                  | The Strawberry schema instance                                        |
