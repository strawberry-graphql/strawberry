---
title: FAQ
faq: true
---

# Frequently Asked Questions

## How can I hide a field from GraphQL?

Strawberry provides a `Private` type that can be used to hide fields from
GraphQL, for example, the following code:

```python
import strawberry

@strawberry.type
class User:
    name: str
    age: int
    password: strawberry.Private[str]

@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> User:
        return User(name="Patrick", age=100, password="This is fake")

schema = strawberry.Schema(query=Query)
```

will result in the following schema:

```graphql
type Query {
  user: User!
}

type User {
  name: String!
  age: Int!
}
```

## How can I deal with circular imports?

In cases where you have circular imports, you can use `strawberry.lazy` to
resolve the circular imports, for example:

```python
# posts.py
from typing import TYPE_CHECKING, Annotated

import strawberry

if TYPE_CHECKING:
    from .users import User

@strawberry.type
class Post:
    title: str
    author: Annotated["User", strawberry.lazy(".users")]
```

For more information, see the [Lazy types](./types/lazy.md) documentation.

## Can I reuse Object Types with Input Objects?

Unfortunately not because, as the
[GraphQL spec](https://spec.graphql.org/June2018/#sec-Input-Objects) specifies,
there is a difference between Objects Types and Inputs types:

> The GraphQL Object type (ObjectTypeDefinition) defined above is inappropriate
> for re‐use here, because Object types can contain fields that define arguments
> or contain references to interfaces and unions, neither of which is
> appropriate for use as an input argument. For this reason, input objects have
> a separate type in the system.

And this is also true for Input types' fields: you can only use Strawberry Input
types or scalar.

See our [Input Types](../types/input-types.md) docs.

## Can I use asyncio with Strawberry and Django?

Yes, we do! Strawberry provides an async view taht you can use with Django 3.1+!
Check [Async Django](../integrations/django.md#async-django) for more
information.

## How can I do authentication with Strawberry?

Authentication is a task that should be handled by the framework, and you should
check its documentation about how to do it. Strawberry it's only a wrapper
around your authentication logic.

You should check our [Authentication](../guides/authentication.md) docs to
understand how to deal with authentication with Strawberry, but TL;TR you should
define a mutation that authenticate the user and then use
[`Permissions` classes](./permissions.md).
