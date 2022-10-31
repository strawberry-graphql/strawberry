---
title: Generics
---

# Generics

Strawberry supports Python's generics types, which can be used to create
reusable types. Let's take a look at an example:

```python
import strawberry

from typing import Generic, TypeVar, List

T = TypeVar('T')

@strawberry.type
class Page(Generic[T]):
    number: int
    items: List[T]
```

This example defines a generic type `Page` that can be used to create a page of
any type. For example, we can create a page of `User` objects:

```python+schema
import strawberry

@strawberry.type
class User:
    name: str

@strawberry.type
class Query:
    users: Page[User]
---
type Query {
  users: UserPage!
}

type User {
  name: String!
}

type UserPage {
  number: Int!
  items: [User!]!
}
```

Strawberry will automatically generate the correct GraphQL schema from the
combination of the generic type and the type arguments.
