---
release type: patch
---

This release fixes generic types that extend several generic types whose type
parameters have the same name.

Strawberry looked up the arguments of type parameters by name across all the
generic bases of a type, so the fields of every base got the arguments of the
first one:

```python
T = TypeVar("T")


@strawberry.type
class Page(Generic[T]):
    first: T


@strawberry.type
class Label(Generic[T]):
    label: T


@strawberry.type
class LabelledPage(Page[int], Label[str]):  # `label` was `Int!`, now `String!`
    pass
```

Each field now gets the arguments of the generic type that declares it. This
also adds support for generic bases whose arguments use the type parameters of
the type extending them, like `class ListBox(Box[list[U]], Generic[U])`, and
fixes fields that wrap a type parameter, like `content: list[T]`, when a
subclass gives it a type like `list[int]`, `int | None` or a lazy type, as in
`class IntListBox(Box[list[int]])`.
