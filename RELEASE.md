---
release type: patch
---

This release fixes the types of fields inherited from generic types, when the
generic types use the same name for their type parameters, or when they're
given a type like `list[T]` or `User | None`.

Strawberry looked up type parameters by name across all the generic types a
type extends, so when two of them called their type parameter `T`, the fields
of both got the type given to the first one:

```python
T = TypeVar("T")


@strawberry.type
class Page(Generic[T]):
    items: list[T]


@strawberry.type
class Sorted(Generic[T]):
    sorted_by: T


@strawberry.type
class UserPage(Page[User], Sorted[UserOrder]):  # `sortedBy` was `User!`
    pass
```

Each inherited field now gets the type given to the generic type that declares
it, so `sortedBy` is `UserOrder!`. This also fixes types that are given to a
type parameter wrapped in a list or an optional:

```python
@strawberry.type
class Result(Generic[T]):
    data: T


@strawberry.type
class ListResult(Result[list[T]], Generic[T]):
    total: int


@strawberry.type
class UserListResult(ListResult[User]):  # `data` was `User!`, now `[User!]!`
    pass


@strawberry.type
class MaybeUserPage(Page[User | None]):  # failed, now `items: [User]!`
    pass
```
