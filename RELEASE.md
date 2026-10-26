---
release type: patch
---

This release fixes generic types that use themselves, and generic types that
use another generic type with one of their own type parameters, like
`Edge[S]` in a `Connection[S]`.

Specializing a generic type that uses itself, directly or through another
generic type, used to fail with a `RecursionError`, as Strawberry created a
new copy of the type each time it found it in one of its fields. Each
specialization is now created once and reused for the fields using it:

```python
T = TypeVar("T")


@strawberry.type
class TreeNode(Generic[T]):
    value: T
    children: list["TreeNode[T]"]


@strawberry.input
class UserFilter:
    name: str


@strawberry.input
class Condition(Generic[T]):
    fields: T | None = None
    conditions: list["Condition[T]"] = strawberry.field(default_factory=list)


@strawberry.type
class Query:
    @strawberry.field
    def tree(self, where: Condition[UserFilter]) -> TreeNode[int]: ...
```

```graphql
type IntTreeNode {
  value: Int!
  children: [IntTreeNode!]!
}

input UserFilterCondition {
  fields: UserFilter = null
  conditions: [UserFilterCondition!]! = []
}
```

A generic type given type parameters of the type using it, like `Edge[S]`
below, was specialized with the arguments of the type using it, looked up by
the name of its own type parameters. So it raised a `KeyError` when their
names were different, and got the wrong arguments when they were swapped,
like in `Pair[S, T]`. Its type parameters now get the arguments it's given:

```python
T = TypeVar("T")
S = TypeVar("S")


@strawberry.type
class Edge(Generic[T]):
    node: T


@strawberry.type
class Connection(Generic[S]):
    edges: list[Edge[S]]


@strawberry.type
class Query:
    connection: Connection[int]
```

```graphql
type IntConnection {
  edges: [IntEdge!]!
}
```
