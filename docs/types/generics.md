---
title: Generics
---

# Generics

Strawberry supports using Python's `Generic` typing to dynamically create
reusable types.

Strawberry will automatically generate the correct GraphQL schema from the
combination of the generic type and the type arguments. Generics are supported
in Object types, Input types, and Arguments to queries, mutations, and scalars.

Let's take a look at an example:

# Object Types

```python
from typing import Generic, List, TypeVar

import strawberry

T = TypeVar("T")


@strawberry.type
class Page(Generic[T]):
    number: int
    items: List[T]
```

This example defines a generic type `Page` that can be used to represent a page
of any type. For example, we can create a page of `User` objects:

<CodeGrid>

```python
import strawberry


@strawberry.type
class User:
    name: str


@strawberry.type
class Query:
    users: Page[User]
```

```graphql
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

</CodeGrid>

It is also possible to use a specialized generic type directly. For example, the
same example above could be written like this:

<CodeGrid>

```python
import strawberry


@strawberry.type
class User:
    name: str


@strawberry.type
class UserPage(Page[User]): ...


@strawberry.type
class Query:
    users: UserPage
```

```graphql
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

</CodeGrid>

# Input and Argument Types

Arguments to queries and mutations can also be made generic by creating Generic
Input types. Here we'll define an input type that can serve as a collection of
anything, then create a specialization by using as a filled-in argument on a
mutation.

<CodeGrid>

```python
import strawberry
from typing import Generic, List, Optional, TypeVar

T = TypeVar("T")


@strawberry.input
class CollectionInput(Generic[T]):
    values: List[T]


@strawberry.input
class PostInput:
    name: str


@strawberry.type
class Post:
    id: int
    name: str


@strawberry.type
class Mutation:
    @strawberry.mutation
    def add_posts(self, posts: CollectionInput[PostInput]) -> bool:
        return True


@strawberry.type
class Query:
    most_recent_post: Optional[Post] = None


schema = strawberry.Schema(query=Query, mutation=Mutation)
```

```graphql
input PostInputCollectionInput {
  values: [PostInput!]!
}

input PostInput {
  name: String!
}

type Post {
  id: Int!
  name: String!
}

type Query {
  mostRecentPost: Post
}

type Mutation {
  addPosts(posts: PostInputCollectionInput!): Boolean!
}
```

</CodeGrid>

> **Note**: Pay attention to the fact that both `CollectionInput` and
> `PostInput` are Input types. Providing `posts: CollectionInput[Post]` to
> `add_posts` (i.e. using the non-input `Post` type) would have resulted in an
> error:
>
> ```
> PostCollectionInput fields cannot be resolved. Input field type must be a
> GraphQL input type
> ```

# Multiple Specializations

Using multiple specializations of a Generic type will work as expected. Here we
define a `Point2D` type and then specialize it for both `int`s and `float`s.

<CodeGrid>

```python
from typing import Generic, TypeVar

import strawberry

T = TypeVar("T")


@strawberry.input
class Point2D(Generic[T]):
    x: T
    y: T


@strawberry.type
class Mutation:
    @strawberry.mutation
    def store_line_float(self, a: Point2D[float], b: Point2D[float]) -> bool:
        return True

    @strawberry.mutation
    def store_line_int(self, a: Point2D[int], b: Point2D[int]) -> bool:
        return True
```

```graphql
type Mutation {
  storeLineFloat(a: FloatPoint2D!, b: FloatPoint2D!): Boolean!
  storeLineInt(a: IntPoint2D!, b: IntPoint2D!): Boolean!
}

input FloatPoint2D {
  x: Float!
  y: Float!
}

input IntPoint2D {
  x: Int!
  y: Int!
}
```

</CodeGrid>

# Variadic Generics

Variadic Generics, introduced in [PEP-646][pep-646], are currently unsupported.

[pep-646]: https://peps.python.org/pep-0646/
